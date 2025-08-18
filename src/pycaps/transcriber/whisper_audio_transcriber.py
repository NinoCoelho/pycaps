from .base_transcriber import AudioTranscriber
from typing import Optional, Any, List
from pycaps.common import Document, Segment, Line, Word, TimeFragment
from pycaps.logger import logger
import re

class WhisperAudioTranscriber(AudioTranscriber):
    def __init__(self, model_size: str = "medium", language: Optional[str] = None, model: Optional[Any] = None, 
                 initial_prompt: Optional[str] = None, portuguese_vocabulary: Optional[List[str]] = None):
        """
        Transcribes audio using OpenAI's Whisper model with Portuguese optimizations.

        Args:
            model_size: Size of the Whisper model to use (e.g., "tiny", "base", "medium").
            language: Language of the audio (e.g., "en", "pt").
            model: (Optional) A pre-loaded Whisper model instance. If provided, model_size is ignored.
            initial_prompt: Custom prompt to guide transcription (max 244 tokens).
            portuguese_vocabulary: List of Portuguese compound/religious terms to recognize.
        """
        self._model_size = model_size
        self._language = language
        self._model = model
        self._initial_prompt = initial_prompt
        self._portuguese_vocabulary = portuguese_vocabulary or []

    def _build_portuguese_prompt(self) -> str:
        """Build optimized prompt for Portuguese compound and religious terms."""
        base_prompt = "Transcrição em português brasileiro."
        
        # Common religious/biblical vocabulary that gets misrecognized
        religious_terms = [
            "Getsêmani", "ajoelhou-se", "prostrou-se", "Jerusalém", "bem-aventurança",
            "auto-sacrifício", "cruz-sagrada", "pós-ressurreição", "ressuscitou",
            "anti-cristo", "sub-reino", "sobre-humano", "bendisse-o", "chamou-se"
        ]
        
        # Add user-provided vocabulary
        all_terms = religious_terms + self._portuguese_vocabulary
        
        if all_terms:
            # Format as examples in the prompt
            examples = ", ".join(all_terms[:15])  # Limit to stay under 244 tokens
            vocabulary_prompt = f" Vocabulário: {examples}."
            
            # Ensure we stay under 244 token limit
            full_prompt = base_prompt + vocabulary_prompt
            if len(full_prompt.split()) > 200:  # Conservative token estimate
                full_prompt = base_prompt + f" Vocabulário: {', '.join(all_terms[:8])}."
                
            return full_prompt
        
        return base_prompt

    def _post_process_portuguese_compounds(self, document: Document) -> Document:
        """Post-process document to fix Portuguese compound word splitting."""
        # Common Portuguese compound word patterns
        compound_patterns = {
            # Reflexive verbs - most common issue
            r'\b(\w+)\s+se\b': r'\1-se',
            r'\b(\w+)\s+me\b': r'\1-me', 
            r'\b(\w+)\s+te\b': r'\1-te',
            r'\b(\w+)\s+nos\b': r'\1-nos',
            r'\b(\w+)\s+lhe\b': r'\1-lhe',
            r'\b(\w+)\s+lhes\b': r'\1-lhes',
            
            # Common prefixes split incorrectly
            r'\bbem\s+(\w+)': r'bem-\1',
            r'\bmal\s+(\w+)': r'mal-\1',
            r'\bauto\s+(\w+)': r'auto-\1',
            r'\banti\s+(\w+)': r'anti-\1',
            r'\bpós\s+(\w+)': r'pós-\1',
            r'\bpré\s+(\w+)': r'pré-\1',
            r'\bsobre\s+(\w+)': r'sobre-\1',
            r'\bsub\s+(\w+)': r'sub-\1',
        }
        
        # Specific religious/biblical terms that get misrecognized
        religious_corrections = {
            "jet semany": "Getsêmani",
            "jet sê mani": "Getsêmani", 
            "get semany": "Getsêmani",
            "jets emany": "Getsêmani",
            "jet semani": "Getsêmani",
            "bem aventurança": "bem-aventurança",
            "bem aventurado": "bem-aventurado",
            "cruz sagrada": "cruz-sagrada",
            "pós ressurreição": "pós-ressurreição",
        }

        # Process each segment
        for segment in document.segments:
            for line in segment.lines:
                # Collect all words in the line for context processing
                words_text = [word.text for word in line.words]
                full_line_text = " ".join(words_text)
                
                # Apply religious/biblical corrections first (case insensitive)
                corrected_text = full_line_text
                for incorrect, correct in religious_corrections.items():
                    corrected_text = re.sub(re.escape(incorrect), correct, corrected_text, flags=re.IGNORECASE)
                
                # Apply compound word patterns
                for pattern, replacement in compound_patterns.items():
                    corrected_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)
                
                # If text changed, update words
                if corrected_text != full_line_text:
                    logger().debug(f"Portuguese correction: '{full_line_text}' -> '{corrected_text}'")
                    corrected_words = corrected_text.split()
                    
                    # Update word texts while preserving timing
                    for i, word in enumerate(line.words):
                        if i < len(corrected_words):
                            word.text = corrected_words[i]
        
        return document

    def transcribe(self, audio_path: str) -> Document:
        """
        Transcribes the audio file and returns segments with timestamps.
        """
        # Build appropriate prompt for Portuguese optimization
        prompt = self._initial_prompt
        if not prompt and (self._language == "pt" or not self._language):
            prompt = self._build_portuguese_prompt()
        
        # Enhanced Whisper parameters for better accuracy
        result = self._get_model().transcribe(
            audio_path,
            word_timestamps=True,
            language=self._language,
            verbose=False, # TODO: we should pass our --verbose param here
            initial_prompt=prompt,
            temperature=0.0,  # More deterministic output
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6
        )

        if "segments" not in result or not result["segments"]:
            logger().warning("Whisper returned no segments in the transcription.")
            return Document()

        logger().debug(f"Whisper result: {result}")
        document = Document()
        for segment_info in result["segments"]:
            segment_start = float(segment_info["start"])
            segment_end = float(segment_info["end"])
            if segment_start == segment_end:
                segment_end = segment_start + 0.01
            segment_time = TimeFragment(start=segment_start, end=segment_end)
            segment = Segment(time=segment_time)
            line = Line(time=segment_time)
            segment.lines.add(line)

            if not "words" in segment_info or not isinstance(segment_info["words"], list):
                logger().debug(f"Segment '{segment_info['text']}' has no detailed word data.")
                continue

            for word_entry in segment_info["words"]:
                # Ensure 'word' is a string, sometimes Whisper might return non-string for certain symbols.
                word_text = str(word_entry["word"]).strip()
                if not word_text:
                    continue

                word_start = float(word_entry["start"])
                word_end = float(word_entry["end"])
                if word_start == word_end:
                    word_end = word_start + 0.01
                word_time = TimeFragment(start=word_start, end=word_end)
                word = Word(text=word_text, time=word_time)
                line.words.add(word) # so far is everything in one single line (we split it in next steps of the pipeline)

            document.segments.add(segment)
        
        if not document.segments:
            logger().warning("No valid segments were processed from Whisper's transcription.")

        # Apply Portuguese post-processing if language is Portuguese or not specified
        if self._language == "pt" or not self._language:
            logger().debug("Applying Portuguese compound word post-processing...")
            document = self._post_process_portuguese_compounds(document)

        return document 

    def _get_model(self):
        if self._model:
            return self._model
        
        import whisper

        try:
            self._model = whisper.load_model(self._model_size)
            return self._model
        except Exception as e:
            raise RuntimeError(
                f"Error loading Whisper model (size: {self._model_size}): {e}\n" 
                f"Ensure Whisper is installed and models are available (or can be downloaded)."
            )