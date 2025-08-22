"""Faster-Whisper transcriber with better hallucination prevention."""

import logging
from typing import Optional, List, Dict, Any
from faster_whisper import WhisperModel
from faster_whisper.vad import get_vad_model, VadOptions
import numpy as np
from ..common.models import Document, Segment, Word, TimeFragment
from ..common.element_container import ElementContainer
from .base_transcriber import AudioTranscriber

logger = logging.getLogger(__name__)


class FasterWhisperTranscriber(AudioTranscriber):
    """
    Transcriber using faster-whisper with built-in anti-hallucination features.
    
    Key advantages:
    - 4x faster than OpenAI Whisper
    - Built-in VAD support
    - Better handling of silence
    - Reduced hallucinations
    - Lower memory usage
    """
    
    def __init__(
        self, 
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "default",
        language: Optional[str] = None,
        use_vad: bool = True,
        vad_threshold: float = 0.5,
        vad_min_speech_duration_ms: int = 250,
        vad_max_speech_duration_s: int = float('inf'),
        hallucination_silence_threshold: Optional[float] = 2.0,
        condition_on_previous_text: bool = False,  # Key: disable to prevent hallucinations
        initial_prompt: Optional[str] = None,
        temperature: float = 0.0,  # Deterministic for consistency
        compression_ratio_threshold: float = 2.4,
        log_prob_threshold: float = -1.0,
        no_speech_threshold: float = 0.6,
        repetition_penalty: float = 1.1  # Penalize repetitions
    ):
        """Initialize faster-whisper transcriber with anti-hallucination settings."""
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.use_vad = use_vad
        self.vad_options = None
        self.hallucination_silence_threshold = hallucination_silence_threshold
        self.condition_on_previous_text = condition_on_previous_text
        self.initial_prompt = initial_prompt
        self.temperature = temperature
        self.compression_ratio_threshold = compression_ratio_threshold
        self.log_prob_threshold = log_prob_threshold
        self.no_speech_threshold = no_speech_threshold
        self.repetition_penalty = repetition_penalty
        
        # Initialize VAD options if enabled
        if self.use_vad:
            self.vad_options = VadOptions(
                threshold=vad_threshold,
                min_speech_duration_ms=vad_min_speech_duration_ms,
                max_speech_duration_s=vad_max_speech_duration_s,
                min_silence_duration_ms=1000,
                speech_pad_ms=400
            )
        
        # Load model
        self._model = None
        
    def _get_model(self) -> WhisperModel:
        """Lazy load the model."""
        if self._model is None:
            logger.info(f"Loading faster-whisper model: {self.model_size}")
            self._model = WhisperModel(
                self.model_size, 
                device=self.device,
                compute_type=self.compute_type
            )
        return self._model
    
    def transcribe(self, audio_path: str) -> Document:
        """
        Transcribe audio using faster-whisper with anti-hallucination measures.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Document with transcribed segments
        """
        model = self._get_model()
        
        # Get VAD model if enabled
        vad_model = get_vad_model() if self.use_vad else None
        
        logger.info(f"Transcribing with faster-whisper (VAD: {self.use_vad})")
        
        # Transcribe with optimal settings
        segments, info = model.transcribe(
            audio_path,
            language=self.language,
            task="transcribe",
            beam_size=5,
            best_of=5,
            patience=1.0,
            length_penalty=1.0,
            repetition_penalty=self.repetition_penalty,
            no_repeat_ngram_size=0,
            temperature=self.temperature,
            compression_ratio_threshold=self.compression_ratio_threshold,
            log_prob_threshold=self.log_prob_threshold,
            no_speech_threshold=self.no_speech_threshold,
            condition_on_previous_text=self.condition_on_previous_text,
            initial_prompt=self.initial_prompt,
            prefix=None,
            suppress_blank=True,
            suppress_tokens=[-1],
            without_timestamps=False,
            max_initial_timestamp=1.0,
            word_timestamps=True,
            prepend_punctuations="\"'([{-",
            append_punctuations="\"'.。,，!！?？:：)]}",
            vad_filter=self.use_vad,
            vad_parameters=self.vad_options,
            hallucination_silence_threshold=self.hallucination_silence_threshold
        )
        
        # Convert to Document format
        document = Document()
        
        for segment_data in segments:
            # Check for potential hallucinations
            if self._is_likely_hallucination(segment_data):
                logger.warning(f"Skipping likely hallucination: {segment_data.text}")
                continue
            
            # Create segment with words
            words = []
            if hasattr(segment_data, 'words') and segment_data.words:
                for word_data in segment_data.words:
                    word = Word(
                        text=word_data.word.strip(),
                        time=TimeFragment(start=word_data.start, end=word_data.end)
                    )
                    words.append(word)
            
            # Create segment - need to create lines with words
            segment = Segment(
                time=TimeFragment(start=segment_data.start, end=segment_data.end)
            )
            
            # Create a line and add words to it
            from ..common.models import Line
            line = Line(time=TimeFragment(start=segment_data.start, end=segment_data.end))
            segment._lines.add(line)
            
            # Add words to the line
            for word in words:
                line._words.add(word)
            
            document._segments.add(segment)
        
        # Post-process to remove any remaining repetitions
        document = self._remove_repetitions(document)
        
        logger.info(f"Transcribed {len(document._segments)} segments with faster-whisper")
        
        return document
    
    def _is_likely_hallucination(self, segment) -> bool:
        """
        Check if a segment is likely a hallucination.
        
        Common hallucination patterns:
        - Very high compression ratio
        - Very low average log probability
        - Common YouTube phrases
        - Excessive repetition
        """
        text = segment.text.lower().strip()
        
        # Check for common hallucination phrases
        hallucination_phrases = [
            "thanks for watching",
            "please subscribe",
            "like and subscribe",
            "subtitles by",
            "amara.org",
            "transcript by",
            "[music]",
            "[applause]",
            "copyright",
            "all rights reserved"
        ]
        
        for phrase in hallucination_phrases:
            if phrase in text:
                return True
        
        # Check compression ratio if available
        if hasattr(segment, 'compression_ratio') and segment.compression_ratio > 2.4:
            return True
        
        # Check average log probability if available
        if hasattr(segment, 'avg_logprob') and segment.avg_logprob < -1.0:
            return True
        
        # Check for excessive repetition (same word repeated many times)
        words = text.split()
        if len(words) > 3:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            max_repetition = max(word_counts.values())
            if max_repetition > len(words) * 0.5:  # More than 50% is same word
                return True
        
        return False
    
    def _remove_repetitions(self, document: Document) -> Document:
        """Remove repetitive segments from document."""
        # For now, skip repetition removal to avoid errors
        # TODO: Implement proper repetition removal with ElementContainer
        return document
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity ratio."""
        if not text1 or not text2:
            return 0.0
        
        # Simple character-based similarity
        longer = max(len(text1), len(text2))
        if longer == 0:
            return 1.0
        
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(text1, text2))
        return matches / longer