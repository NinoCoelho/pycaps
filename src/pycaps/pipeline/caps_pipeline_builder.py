import os
from .caps_pipeline import CapsPipeline
from pycaps.layout import SubtitleLayoutOptions, LineSplitter, LayoutUpdater, PositionsCalculator
from pycaps.transcriber import AudioTranscriber, BaseSegmentSplitter, WhisperAudioTranscriber, PreviewTranscriber, SRTTranscriber, TranslationTranscriber
from pycaps.transcriber.anti_hallucination_config import AntiHallucinationConfig
from typing import Union
from typing import Optional, List
from pycaps.animation import Animation, ElementAnimator
from pycaps.common import ElementType, EventType, VideoQuality, CacheStrategy
from pycaps.tag import TagCondition, SemanticTagger, StructureTagger
from pycaps.effect import TextEffect, ClipEffect, SoundEffect, Effect
from pycaps.logger import logger
from pycaps.renderer import SubtitleRenderer

class CapsPipelineBuilder:

    def __init__(self):
        self._caps_pipeline: CapsPipeline = CapsPipeline()
    
    def with_input_video(self, input_video_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(input_video_path):
            raise ValueError(f"Input video file not found: {input_video_path}")
        self._caps_pipeline._input_video_path = input_video_path
        return self
    
    def with_output_video(self, output_video_path: str) -> "CapsPipelineBuilder":
        if os.path.exists(output_video_path):
            raise ValueError(f"Output video path already exists: {output_video_path}")
        self._caps_pipeline._output_video_path = output_video_path
        return self

    def with_resources(self, resources_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(resources_path):
            raise ValueError(f"Resources path does not exist: {resources_path}")
        if not os.path.isdir(resources_path):
            raise ValueError(f"Resources path is not a directory: {resources_path}")
        self._caps_pipeline._resources_dir = resources_path
        return self
    
    def with_video_quality(self, quality: VideoQuality) -> "CapsPipelineBuilder":
        self._caps_pipeline._video_generator.set_video_quality(quality)
        return self
    
    def with_layout_options(self, layout_options: SubtitleLayoutOptions) -> "CapsPipelineBuilder":
        self._caps_pipeline._layout_options = layout_options
        return self
    
    def add_css(self, css_file_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(css_file_path):
            raise ValueError(f"CSS file not found: {css_file_path}")
        css_content = open(css_file_path, "r", encoding="utf-8").read()
        self._caps_pipeline._renderer.append_css(css_content)
        return self
    
    def add_css_content(self, css_content: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._renderer.append_css(css_content)
        return self

    def with_custom_subtitle_renderer(self, subtitle_renderer: SubtitleRenderer) -> "CapsPipelineBuilder":
        self._caps_pipeline._renderer = subtitle_renderer
        return self
    
    def with_whisper_config(self, language: Optional[str] = None, model_size: str = "medium", 
                           initial_prompt: Optional[str] = None, portuguese_vocabulary: Optional[List[str]] = None,
                           anti_hallucination_config: Optional[Union[AntiHallucinationConfig, str]] = "balanced") -> "CapsPipelineBuilder":
        """Configure Whisper transcriber with anti-hallucination features.
        
        Args:
            language: Language code (e.g., "pt", "en") or None for auto-detection
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large", "large-v2", "large-v3")
            initial_prompt: Custom prompt for transcription
            portuguese_vocabulary: List of Portuguese terms for better recognition
            anti_hallucination_config: Anti-hallucination preset or config object:
                - "maximum_quality": Best quality, slower processing
                - "balanced": Good quality with reasonable speed (default)
                - "fast_processing": Faster processing, basic filtering
                - "podcasts": Optimized for long-form audio content
                - "short_videos": Optimized for short-form content
                - AntiHallucinationConfig object: Custom configuration
        """
        self._caps_pipeline._transcriber = WhisperAudioTranscriber(
            model_size=model_size, 
            language=language,
            initial_prompt=initial_prompt,
            portuguese_vocabulary=portuguese_vocabulary,
            anti_hallucination_config=anti_hallucination_config
        )
        return self
    
    def with_anti_hallucination_preset(self, preset: str) -> "CapsPipelineBuilder":
        """Set anti-hallucination preset for the current transcriber.
        
        Args:
            preset: One of "maximum_quality", "balanced", "fast_processing", "podcasts", "short_videos"
        """
        if isinstance(self._caps_pipeline._transcriber, WhisperAudioTranscriber):
            # Update existing transcriber with new preset
            current = self._caps_pipeline._transcriber
            self._caps_pipeline._transcriber = WhisperAudioTranscriber(
                model_size=current._model_size,
                language=current._language,
                initial_prompt=current._initial_prompt,
                portuguese_vocabulary=current._portuguese_vocabulary,
                anti_hallucination_config=preset
            )
        else:
            # Create new WhisperAudioTranscriber with preset
            self._caps_pipeline._transcriber = WhisperAudioTranscriber(
                anti_hallucination_config=preset
            )
        return self
    
    def with_faster_whisper(
        self,
        model_size: str = "base",
        language: str = None,
        use_vad: bool = True,
        hallucination_silence_threshold: float = 2.0
    ) -> "CapsPipelineBuilder":
        """Use faster-whisper for transcription (4x faster, less hallucinations).
        
        Args:
            model_size: Model size (tiny, base, small, medium, large-v2, large-v3)
            language: Language code (e.g., 'en', 'pt')
            use_vad: Enable Voice Activity Detection
            hallucination_silence_threshold: Skip silence longer than threshold
        
        Returns:
            Self for method chaining
        """
        from ..transcriber.faster_whisper_transcriber import FasterWhisperTranscriber
        
        self._caps_pipeline._transcriber = FasterWhisperTranscriber(
            model_size=model_size,
            language=language,
            use_vad=use_vad,
            hallucination_silence_threshold=hallucination_silence_threshold,
            condition_on_previous_text=False,  # Disable to prevent hallucinations
            temperature=0.0,  # Deterministic
            repetition_penalty=1.1  # Penalize repetitions
        )
        return self
    
    def with_translation(
        self,
        source_language: str = "en",
        target_language: str = "pt",
        transcriber_type: str = "faster_whisper",
        model_size: str = "base",
        translation_provider: str = "deepl",
        deepl_api_key: Optional[str] = None,
        max_line_length: int = 42,
        reading_speed: int = 17,
        enable_context_translation: bool = True
    ) -> "CapsPipelineBuilder":
        """Configure pipeline for English-to-Portuguese translation.
        
        This method enables high-precision translation using the enhanced
        specification from english-portuguese-enhancement.md.
        
        Args:
            source_language: Source language code (e.g., "en")
            target_language: Target language code (e.g., "pt", "pt-BR") 
            transcriber_type: "whisper" or "faster_whisper" (recommended)
            model_size: Whisper model size for transcription
            translation_provider: "deepl" (recommended) or "google"
            deepl_api_key: DeepL API key (optional, can use env var DEEPL_API_KEY)
            max_line_length: Maximum characters per line for Portuguese (Netflix: 42)
            reading_speed: Reading speed in chars/second for Portuguese (17-20)
            enable_context_translation: Use context-aware batch translation
            
        Returns:
            Self for method chaining
            
        Example:
            pipeline = (CapsPipelineBuilder()
                .with_input_video("english_video.mp4")
                .with_translation(
                    source_language="en",
                    target_language="pt-BR", 
                    translation_provider="deepl",
                    deepl_api_key="your-key"
                )
                .with_output_video("portuguese_subtitles.mp4")
                .build())
        """
        self._caps_pipeline._transcriber = TranslationTranscriber(
            transcriber_type=transcriber_type,
            model_size=model_size,
            source_language=source_language,
            target_language=target_language,
            translation_provider=translation_provider,
            deepl_api_key=deepl_api_key,
            max_line_length=max_line_length,
            reading_speed=reading_speed,
            enable_context_translation=enable_context_translation
        )
        return self
    
    def with_portuguese_translation(
        self,
        transcriber_type: str = "faster_whisper",
        model_size: str = "base", 
        variant: str = "pt",  # "pt" for European, "pt-BR" for Brazilian
        translation_provider: str = "deepl",
        deepl_api_key: Optional[str] = None
    ) -> "CapsPipelineBuilder":
        """Convenience method for English-to-Portuguese translation.
        
        Configures optimal settings for Portuguese subtitle generation
        based on the enhanced specification.
        
        Args:
            transcriber_type: "whisper" or "faster_whisper" (recommended for 4x speed)
            model_size: Whisper model ("base", "medium", "large-v3")
            variant: "pt" for European Portuguese, "pt-BR" for Brazilian
            translation_provider: "deepl" (higher quality) or "google" (free)
            deepl_api_key: DeepL API key (optional)
            
        Returns:
            Self for method chaining
        """
        # Configure Portuguese-specific settings
        max_line_length = 42 if variant == "pt-BR" else 40  # Netflix vs European standards
        reading_speed = 17 if variant == "pt-BR" else 18    # Brazilian vs European reading speeds
        
        return self.with_translation(
            source_language="en",
            target_language=variant,
            transcriber_type=transcriber_type,
            model_size=model_size,
            translation_provider=translation_provider,
            deepl_api_key=deepl_api_key,
            max_line_length=max_line_length,
            reading_speed=reading_speed,
            enable_context_translation=True
        )
    
    def with_custom_audio_transcriber(self, audio_transcriber: AudioTranscriber) -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = audio_transcriber
        return self
    
    def with_cache_strategy(self, cache_strategy: CacheStrategy) -> "CapsPipelineBuilder":
        self._caps_pipeline._cache_strategy = cache_strategy
        return self

    def with_subtitle_data_path(self, subtitle_data_path: str) -> "CapsPipelineBuilder":
        if subtitle_data_path and not os.path.exists(subtitle_data_path):
            raise ValueError(f"Subtitle data file not found: {subtitle_data_path}")
        self._caps_pipeline._subtitle_data_path_for_loading = subtitle_data_path
        return self
    
    def with_srt_file(self, srt_file_path: str) -> "CapsPipelineBuilder":
        """Configure pipeline to use SRT subtitle file instead of audio transcription."""
        if srt_file_path and not os.path.exists(srt_file_path):
            raise ValueError(f"SRT file not found: {srt_file_path}")
        # Create SRT transcriber and set it as the transcriber
        srt_transcriber = SRTTranscriber(srt_file_path)
        self._caps_pipeline._transcriber = srt_transcriber
        # Skip saving subtitle data since we're loading from SRT
        self.should_save_subtitle_data(False)
        return self
    
    def should_save_subtitle_data(self, should_save: bool) -> "CapsPipelineBuilder":
        self._caps_pipeline._should_save_subtitle_data = should_save
        return self
    
    def should_preview_transcription(self, should_preview: bool) -> "CapsPipelineBuilder":
        self._caps_pipeline._should_preview_transcription = should_preview
        return self
    
    def add_segment_splitter(self, segment_splitter: BaseSegmentSplitter) -> "CapsPipelineBuilder":
        self._caps_pipeline._segment_splitters.append(segment_splitter)
        return self
    
    def with_semantic_tagger(self, semantic_tagger: SemanticTagger) -> "CapsPipelineBuilder":
        self._caps_pipeline._semantic_tagger = semantic_tagger
        return self
    
    def with_structure_tagger(self, structure_tagger: StructureTagger) -> "CapsPipelineBuilder":
        self._caps_pipeline._structure_tagger = structure_tagger
        return self  
    
    def add_animation(self, animation: Animation, when: EventType, what: ElementType, tag_condition: Optional[TagCondition] = None) -> "CapsPipelineBuilder":
        self._caps_pipeline._animators.append(ElementAnimator(animation, when, what, tag_condition)) 
        return self
    
    def add_effect(self, effect: Effect) -> "CapsPipelineBuilder":
        if isinstance(effect, TextEffect):
            self._caps_pipeline._text_effects.append(effect)
        elif isinstance(effect, ClipEffect):
            self._caps_pipeline._clip_effects.append(effect)
        elif isinstance(effect, SoundEffect):
            self._caps_pipeline._sound_effects.append(effect)
        return self

    def build(self, preview_time: Optional[tuple[float, float]] = None) -> CapsPipeline:
        if not self._caps_pipeline._input_video_path:
            raise ValueError("Input video path is required")
        if preview_time:
            # Check if we're using an SRT transcriber - if so, preserve it and don't use dummy text
            using_srt = isinstance(self._caps_pipeline._transcriber, SRTTranscriber)
            if using_srt:
                logger().warning("Generating preview with SRT content and reduced quality to save time.")
            else:
                logger().warning("Generating preview: using dummy text and reducing quality to save time.")
                self.with_custom_audio_transcriber(PreviewTranscriber())
            
            self.with_video_quality(VideoQuality.LOW)
            self.should_save_subtitle_data(False)
            self._caps_pipeline._preview_time = preview_time
        
        pipeline = self._caps_pipeline
        self._caps_pipeline = CapsPipeline()
        return pipeline