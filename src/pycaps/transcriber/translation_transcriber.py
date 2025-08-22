"""Translation transcriber for English-to-Portuguese subtitle generation."""

import logging
from typing import Optional, List, Dict, Any, Union
from ..common.models import Document, Segment, Line, Word, TimeFragment
from ..common.element_container import ElementContainer
from .base_transcriber import AudioTranscriber
from .whisper_audio_transcriber import WhisperAudioTranscriber
from .faster_whisper_transcriber import FasterWhisperTranscriber
from .translation_service import TranslationService, TranslationError, TranslationServiceUnavailable
from .deepl_translation_service import DeepLTranslationService
from .google_translation_service import GoogleTranslationService
from .translation_quality_validator import TranslationQualityValidator

logger = logging.getLogger(__name__)


class TranslationTranscriber(AudioTranscriber):
    """
    Transcriber that combines speech recognition with translation for
    high-precision English-to-Portuguese subtitle generation.
    
    This transcriber implements the enhanced specification from
    english-portuguese-enhancement.md with professional-grade features:
    - WhisperX/Faster-Whisper for accurate transcription
    - DeepL/Google Translate for professional translation
    - Portuguese-specific subtitle formatting
    - Context-aware translation batching
    - Quality validation and error recovery
    """
    
    def __init__(
        self,
        # Transcription settings
        transcriber_type: str = "faster_whisper",  # "whisper" or "faster_whisper"
        model_size: str = "base",
        source_language: str = "en",
        target_language: str = "pt",
        
        # Translation settings
        translation_provider: str = "deepl",  # "deepl" or "google"
        deepl_api_key: Optional[str] = None,
        
        # Portuguese-specific settings
        max_line_length: int = 42,  # Netflix standard for Portuguese
        max_lines: int = 2,
        reading_speed: int = 17,  # Characters per second for Portuguese
        max_duration: float = 6.0,
        min_duration: float = 1.0,
        
        # Quality settings
        save_original_transcription: bool = True,
        enable_context_translation: bool = True,
        batch_size: int = 5
    ):
        """
        Initialize translation transcriber.
        
        Args:
            transcriber_type: "whisper" or "faster_whisper"
            model_size: Whisper model size
            source_language: Source language code (e.g., "en")
            target_language: Target language code (e.g., "pt", "pt-BR")
            translation_provider: "deepl" or "google"
            deepl_api_key: DeepL API key (optional, can use env var)
            max_line_length: Maximum characters per line for Portuguese
            max_lines: Maximum lines per subtitle
            reading_speed: Reading speed in characters per second
            max_duration: Maximum subtitle duration
            min_duration: Minimum subtitle duration
            save_original_transcription: Keep original English transcription
            enable_context_translation: Use context-aware batch translation
            batch_size: Number of segments to translate together
        """
        self.transcriber_type = transcriber_type
        self.model_size = model_size
        self.source_language = source_language
        self.target_language = target_language
        self.translation_provider = translation_provider
        self.deepl_api_key = deepl_api_key
        
        # Portuguese formatting settings
        self.max_line_length = max_line_length
        self.max_lines = max_lines
        self.reading_speed = reading_speed
        self.max_duration = max_duration
        self.min_duration = min_duration
        
        # Quality settings
        self.save_original_transcription = save_original_transcription
        self.enable_context_translation = enable_context_translation
        self.batch_size = batch_size
        
        # Initialize components
        self._speech_transcriber = None
        self._translation_service = None
        
    def _get_speech_transcriber(self) -> AudioTranscriber:
        """Get the speech transcriber instance."""
        if self._speech_transcriber is None:
            if self.transcriber_type == "faster_whisper":
                self._speech_transcriber = FasterWhisperTranscriber(
                    model_size=self.model_size,
                    language=self.source_language,
                    condition_on_previous_text=False,  # Prevent hallucinations
                    temperature=0.0,  # Deterministic
                    use_vad=True  # Better silence handling
                )
            else:
                self._speech_transcriber = WhisperAudioTranscriber(
                    model_size=self.model_size,
                    language=self.source_language
                )
            
            logger.info(f"Initialized {self.transcriber_type} transcriber with model {self.model_size}")
        
        return self._speech_transcriber
    
    def _get_translation_service(self) -> TranslationService:
        """Get the translation service instance."""
        if self._translation_service is None:
            # Try DeepL first if specified
            if self.translation_provider == "deepl":
                try:
                    service = DeepLTranslationService(api_key=self.deepl_api_key)
                    if service.is_available():
                        self._translation_service = service
                        logger.info("Using DeepL translation service")
                    else:
                        logger.warning("DeepL not available, falling back to Google Translate")
                        self._translation_service = GoogleTranslationService()
                except TranslationServiceUnavailable:
                    logger.warning("DeepL initialization failed, falling back to Google Translate")
                    self._translation_service = GoogleTranslationService()
            else:
                # Use Google Translate
                self._translation_service = GoogleTranslationService()
                logger.info("Using Google Translate service")
            
            if not self._translation_service.is_available():
                raise TranslationServiceUnavailable("No translation service is available")
        
        return self._translation_service
    
    def transcribe(self, audio_path: str) -> Document:
        """
        Transcribe audio and translate to target language.
        
        Processing pipeline:
        1. Transcribe audio to source language with word-level timestamps
        2. Extract text segments with proper timing
        3. Translate segments with context preservation
        4. Apply Portuguese-specific formatting optimizations
        5. Validate subtitle quality and timing
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Document with translated segments optimized for Portuguese
        """
        logger.info(f"Starting translation transcription: {self.source_language} -> {self.target_language}")
        
        # Step 1: Transcribe audio to source language
        speech_transcriber = self._get_speech_transcriber()
        original_document = speech_transcriber.transcribe(audio_path)
        
        logger.info(f"Original transcription completed: {len(original_document._segments)} segments")
        
        # Step 2: Extract segments for translation
        segments_to_translate = []
        for segment in original_document._segments:
            # Get segment text
            segment_text = self._extract_segment_text(segment)
            if segment_text.strip():
                segments_to_translate.append({
                    'segment': segment,
                    'text': segment_text,
                    'start_time': segment.time.start,
                    'end_time': segment.time.end
                })
        
        logger.info(f"Extracted {len(segments_to_translate)} segments for translation")
        
        # Step 3: Translate segments
        translated_segments = self._translate_segments(segments_to_translate)
        
        # Step 4: Create translated document
        translated_document = self._create_translated_document(
            original_document, 
            translated_segments
        )
        
        # Step 5: Apply Portuguese optimizations
        optimized_document = self._optimize_for_portuguese(translated_document)
        
        # Step 6: Validate quality
        self._validate_subtitle_quality(optimized_document)
        
        logger.info(f"Translation transcription completed: {len(optimized_document._segments)} final segments")
        
        return optimized_document
    
    def _extract_segment_text(self, segment: Segment) -> str:
        """Extract text from segment."""
        texts = []
        for line in segment._lines:
            line_texts = []
            for word in line._words:
                line_texts.append(word.text)
            if line_texts:
                texts.append(" ".join(line_texts))
        return " ".join(texts)
    
    def _translate_segments(self, segments_to_translate: List[Dict]) -> List[Dict]:
        """Translate segments with context preservation."""
        translation_service = self._get_translation_service()
        
        if self.enable_context_translation and len(segments_to_translate) > 1:
            # Context-aware batch translation
            return self._translate_with_context(segments_to_translate, translation_service)
        else:
            # Individual translation
            return self._translate_individually(segments_to_translate, translation_service)
    
    def _translate_with_context(
        self, 
        segments_to_translate: List[Dict], 
        translation_service: TranslationService
    ) -> List[Dict]:
        """Translate segments in batches to preserve context."""
        translated_segments = []
        
        for i in range(0, len(segments_to_translate), self.batch_size):
            batch = segments_to_translate[i:i + self.batch_size]
            texts_to_translate = [seg['text'] for seg in batch]
            
            try:
                translated_texts = translation_service.translate_batch(
                    texts_to_translate,
                    self.source_language,
                    self.target_language
                )
                
                # Combine translations with original segments
                # Ensure we have exactly the same number of translations as batch items
                if len(translated_texts) != len(batch):
                    logger.warning(f"Mismatch between batch size ({len(batch)}) and translations ({len(translated_texts)})")
                
                for j, translated_text in enumerate(translated_texts):
                    if j < len(batch):  # Safety check
                        segment_info = batch[j].copy()
                        segment_info['translated_text'] = translated_text
                        translated_segments.append(segment_info)
                    else:
                        logger.error(f"Translation index {j} exceeds batch size {len(batch)}")
                
                # Handle case where we got fewer translations than expected
                for j in range(len(translated_texts), len(batch)):
                    logger.warning(f"Missing translation for batch item {j}, using original text")
                    segment_info = batch[j].copy()
                    segment_info['translated_text'] = segment_info['text']  # Keep original
                    translated_segments.append(segment_info)
                
            except TranslationError as e:
                logger.error(f"Batch translation failed: {e}")
                # Fallback to individual translation
                for segment_info in batch:
                    try:
                        translated_text = translation_service.translate(
                            segment_info['text'],
                            self.source_language,
                            self.target_language
                        )
                        segment_info['translated_text'] = translated_text
                        translated_segments.append(segment_info)
                    except TranslationError:
                        # Keep original text as fallback
                        segment_info['translated_text'] = segment_info['text']
                        translated_segments.append(segment_info)
        
        logger.info(f"Context-aware translation completed: {len(translated_segments)} segments")
        return translated_segments
    
    def _translate_individually(
        self, 
        segments_to_translate: List[Dict], 
        translation_service: TranslationService
    ) -> List[Dict]:
        """Translate segments individually."""
        translated_segments = []
        
        for segment_info in segments_to_translate:
            try:
                translated_text = translation_service.translate(
                    segment_info['text'],
                    self.source_language,
                    self.target_language
                )
                segment_info['translated_text'] = translated_text
                translated_segments.append(segment_info)
                
            except TranslationError as e:
                logger.error(f"Translation failed for segment '{segment_info['text']}': {e}")
                # Keep original text as fallback
                segment_info['translated_text'] = segment_info['text']
                translated_segments.append(segment_info)
        
        logger.info(f"Individual translation completed: {len(translated_segments)} segments")
        return translated_segments
    
    def _create_translated_document(
        self, 
        original_document: Document, 
        translated_segments: List[Dict]
    ) -> Document:
        """Create new document with translated content."""
        translated_document = Document()
        
        for segment_info in translated_segments:
            original_segment = segment_info['segment']
            translated_text = segment_info['translated_text']
            
            # Create new segment with translated text
            new_segment = Segment(
                time=TimeFragment(
                    start=segment_info['start_time'],
                    end=segment_info['end_time']
                )
            )
            
            # Create line with translated words
            # For now, we'll create a simple word timing distribution
            words = self._create_translated_words(
                translated_text,
                segment_info['start_time'],
                segment_info['end_time']
            )
            
            if words:
                line = Line(
                    time=TimeFragment(
                        start=segment_info['start_time'],
                        end=segment_info['end_time']
                    )
                )
                
                for word in words:
                    line._words.add(word)
                
                new_segment._lines.add(line)
            
            translated_document._segments.add(new_segment)
        
        return translated_document
    
    def _create_translated_words(
        self, 
        translated_text: str, 
        start_time: float, 
        end_time: float
    ) -> List[Word]:
        """Create word objects with estimated timing for translated text."""
        words_text = translated_text.split()
        if not words_text:
            return []
        
        duration = end_time - start_time
        time_per_word = duration / len(words_text)
        
        words = []
        current_time = start_time
        
        for word_text in words_text:
            word_duration = time_per_word
            
            # Adjust duration based on word length (simple heuristic)
            if len(word_text) > 6:
                word_duration *= 1.2
            elif len(word_text) < 3:
                word_duration *= 0.8
            
            word = Word(
                text=word_text,
                time=TimeFragment(
                    start=current_time,
                    end=min(current_time + word_duration, end_time)
                )
            )
            
            words.append(word)
            current_time += word_duration
        
        return words
    
    def _optimize_for_portuguese(self, document: Document) -> Document:
        """Apply Portuguese-specific subtitle optimizations."""
        logger.info("Applying Portuguese subtitle optimizations")
        
        optimized_document = Document()
        
        for segment in document._segments:
            # Check if segment needs optimization
            segment_text = self._extract_segment_text(segment)
            duration = segment.time.end - segment.time.start
            
            # Calculate reading metrics
            chars_per_second = len(segment_text) / duration if duration > 0 else 0
            needs_split = (
                len(segment_text) > self.max_line_length * self.max_lines or
                duration > self.max_duration or
                chars_per_second > self.reading_speed
            )
            
            if needs_split and len(segment_text.split()) > 1:
                # Split segment for better readability
                split_segments = self._split_segment_for_portuguese(segment)
                for split_segment in split_segments:
                    optimized_document._segments.add(split_segment)
            else:
                # Format existing segment
                formatted_segment = self._format_segment_for_portuguese(segment)
                optimized_document._segments.add(formatted_segment)
        
        # Merge very short segments
        final_document = self._merge_short_segments(optimized_document)
        
        # Fix overlapping timestamps
        final_document = self._fix_overlapping_timestamps(final_document)
        
        logger.info(f"Portuguese optimization completed: {len(final_document._segments)} segments")
        return final_document
    
    def _split_segment_for_portuguese(self, segment: Segment) -> List[Segment]:
        """Split segment for Portuguese readability."""
        # For now, implement simple splitting logic
        # TODO: Add more sophisticated Portuguese sentence splitting
        segment_text = self._extract_segment_text(segment)
        duration = segment.time.end - segment.time.start
        
        # Simple split by length
        words = segment_text.split()
        mid_point = len(words) // 2
        
        first_half = " ".join(words[:mid_point])
        second_half = " ".join(words[mid_point:])
        
        first_duration = duration * 0.5
        second_duration = duration * 0.5
        
        segments = []
        
        if first_half:
            first_words = self._create_translated_words(
                first_half,
                segment.time.start,
                segment.time.start + first_duration
            )
            first_segment = Segment(
                time=TimeFragment(
                    start=segment.time.start,
                    end=segment.time.start + first_duration
                )
            )
            first_line = Line(
                time=TimeFragment(
                    start=segment.time.start,
                    end=segment.time.start + first_duration
                )
            )
            for word in first_words:
                first_line._words.add(word)
            first_segment._lines.add(first_line)
            segments.append(first_segment)
        
        if second_half:
            second_words = self._create_translated_words(
                second_half,
                segment.time.start + first_duration,
                segment.time.end
            )
            second_segment = Segment(
                time=TimeFragment(
                    start=segment.time.start + first_duration,
                    end=segment.time.end
                )
            )
            second_line = Line(
                time=TimeFragment(
                    start=segment.time.start + first_duration,
                    end=segment.time.end
                )
            )
            for word in second_words:
                second_line._words.add(word)
            second_segment._lines.add(second_line)
            segments.append(second_segment)
        
        return segments
    
    def _format_segment_for_portuguese(self, segment: Segment) -> Segment:
        """Format segment text for Portuguese display."""
        # For now, return segment as-is
        # TODO: Add Portuguese-specific formatting rules
        return segment
    
    def _merge_short_segments(self, document: Document) -> Document:
        """Merge segments that are too short."""
        segments_list = list(document._segments)
        if not segments_list:
            return document
        
        merged_document = Document()
        buffer_segment = None
        
        for segment in segments_list:
            duration = segment.time.end - segment.time.start
            
            if duration < self.min_duration and buffer_segment:
                # Merge with previous segment
                buffer_segment = self._merge_two_segments(buffer_segment, segment)
            else:
                if buffer_segment:
                    merged_document._segments.add(buffer_segment)
                buffer_segment = segment
        
        if buffer_segment:
            merged_document._segments.add(buffer_segment)
        
        return merged_document
    
    def _merge_two_segments(self, segment1: Segment, segment2: Segment) -> Segment:
        """Merge two segments into one."""
        text1 = self._extract_segment_text(segment1)
        text2 = self._extract_segment_text(segment2)
        combined_text = f"{text1} {text2}"
        
        merged_words = self._create_translated_words(
            combined_text,
            segment1.time.start,
            segment2.time.end
        )
        
        merged_segment = Segment(
            time=TimeFragment(
                start=segment1.time.start,
                end=segment2.time.end
            )
        )
        
        if merged_words:
            merged_line = Line(
                time=TimeFragment(
                    start=segment1.time.start,
                    end=segment2.time.end
                )
            )
            for word in merged_words:
                merged_line._words.add(word)
            merged_segment._lines.add(merged_line)
        
        return merged_segment
    
    def _fix_overlapping_timestamps(self, document: Document) -> Document:
        """Ensure no timestamp overlaps."""
        segments_list = list(document._segments)
        segments_list.sort(key=lambda s: s.time.start)
        
        for i in range(1, len(segments_list)):
            current_segment = segments_list[i]
            previous_segment = segments_list[i-1]
            
            if current_segment.time.start < previous_segment.time.end:
                # Adjust timestamps with small gap
                gap = 0.1  # 100ms gap
                new_start = previous_segment.time.end + gap
                
                # Update segment timing
                current_segment.time = TimeFragment(
                    start=new_start,
                    end=max(new_start + 0.5, current_segment.time.end)  # Minimum 500ms duration
                )
                
                # Update line and word timings
                for line in current_segment._lines:
                    line.time = TimeFragment(
                        start=new_start,
                        end=current_segment.time.end
                    )
                    # Simple approach: redistribute word timings
                    words_list = list(line._words)
                    if words_list:
                        duration = current_segment.time.end - new_start
                        time_per_word = duration / len(words_list)
                        current_time = new_start
                        
                        for word in words_list:
                            word.time = TimeFragment(
                                start=current_time,
                                end=min(current_time + time_per_word, current_segment.time.end)
                            )
                            current_time += time_per_word
        
        return document
    
    def _validate_subtitle_quality(self, document: Document):
        """Validate subtitle quality using comprehensive metrics."""
        # Create quality validator with our settings
        validator = TranslationQualityValidator(
            max_reading_speed=self.reading_speed,
            max_line_length=self.max_line_length,
            max_duration=self.max_duration,
            min_duration=self.min_duration
        )
        
        # Perform comprehensive validation
        metrics = validator.validate_document(document)
        
        # Log summary metrics
        logger.info(f"Quality validation completed: {metrics.total_segments} segments, "
                   f"quality score: {metrics.overall_quality_score:.2f}")
        
        # Log specific issues
        if metrics.reading_speed_issues > 0:
            logger.warning(f"{metrics.reading_speed_issues} segments exceed reading speed limit "
                          f"({self.reading_speed} chars/sec)")
        
        if metrics.line_length_issues > 0:
            logger.warning(f"{metrics.line_length_issues} lines exceed length limit "
                          f"({self.max_line_length} chars)")
        
        if metrics.duration_issues > 0:
            logger.warning(f"{metrics.duration_issues} segments have duration issues "
                          f"(outside {self.min_duration}-{self.max_duration}s range)")
        
        if metrics.overlapping_segments > 0:
            logger.warning(f"{metrics.overlapping_segments} segments have timing overlaps")
        
        if metrics.empty_translations > 0:
            logger.error(f"{metrics.empty_translations} segments have empty translations")
        
        if metrics.suspicious_translations > 0:
            logger.warning(f"{metrics.suspicious_translations} segments have suspicious translations")
        
        # Generate detailed report for debug logging
        if logger.isEnabledFor(logging.DEBUG):
            report = validator.generate_quality_report(metrics)
            logger.debug(f"Detailed quality report:\n{report}")
        
        # Log overall quality assessment
        if metrics.overall_quality_score >= 0.9:
            logger.info("✅ Translation quality: Excellent")
        elif metrics.overall_quality_score >= 0.8:
            logger.info("✅ Translation quality: Good")
        elif metrics.overall_quality_score >= 0.6:
            logger.warning("⚠️  Translation quality: Moderate - improvements recommended")
        else:
            logger.error("❌ Translation quality: Poor - significant issues detected")
        
        return metrics