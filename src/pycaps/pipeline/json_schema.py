from pycaps.layout import SubtitleLayoutOptions
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pycaps.common import EventType, ElementType, VideoQuality, CacheStrategy
from pycaps.effect import EmojiAlign
from typing import Literal, Annotated, Optional
from pycaps.animation import Direction, OvershootConfig

# TODO: we are copying the default values that receive the classes, we should avoid that
class BaseConfigModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

class VideoConfig(BaseConfigModel):
    quality: Optional[VideoQuality] = None

class WhisperConfig(BaseConfigModel):
    language: Optional[str] = None
    model: Literal["tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en", "large", "large-v2", "large-v3", "turbo"] = "base"
    initial_prompt: Optional[str] = None
    portuguese_vocabulary: Optional[list[str]] = None
    anti_hallucination_preset: Literal["maximum_quality", "balanced", "fast_processing", "podcasts", "short_videos"] = "balanced"

class FasterWhisperConfig(BaseConfigModel):
    model: Literal["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"] = "base"
    language: Optional[str] = None
    device: Literal["auto", "cpu", "cuda"] = "auto"
    compute_type: Literal["default", "int8", "int8_float16", "int16", "float16", "float32"] = "default"
    use_vad: bool = True
    vad_threshold: float = 0.5
    hallucination_silence_threshold: float = 2.0
    condition_on_previous_text: bool = False
    temperature: float = 0.0
    repetition_penalty: float = 1.1

class TranslationConfig(BaseConfigModel):
    source_language: str = "en"
    target_language: str = "pt"
    transcriber_type: Literal["whisper", "faster_whisper"] = "faster_whisper"
    model_size: Literal["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"] = "base"
    translation_provider: Literal["deepl", "google"] = "deepl"
    deepl_api_key: Optional[str] = None
    max_line_length: int = 42
    max_lines: int = 2
    reading_speed: int = 17
    max_duration: float = 6.0
    min_duration: float = 1.0
    save_original_transcription: bool = True
    enable_context_translation: bool = True
    batch_size: int = 5
    
    @field_validator("max_line_length", "max_lines", "reading_speed")
    @classmethod
    def validate_positive_values(cls, v: int, info) -> int:
        if v <= 0:
            raise ValueError(f"{info.field_name} must be greater than 0")
        return v
    
    @field_validator("max_duration", "min_duration")
    @classmethod
    def validate_positive_durations(cls, v: float, info) -> float:
        if v <= 0:
            raise ValueError(f"{info.field_name} must be greater than 0")
        return v
    
    @field_validator("max_duration")
    @classmethod
    def validate_max_duration(cls, v: float, info) -> float:
        min_duration = info.data.get("min_duration")
        if min_duration is not None and v <= min_duration:
            raise ValueError(f"max_duration must be greater than min_duration ({min_duration})")
        return v

class PortugueseTranslationConfig(BaseConfigModel):
    transcriber_type: Literal["whisper", "faster_whisper"] = "faster_whisper"
    model_size: Literal["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"] = "base"
    variant: Literal["pt", "pt-BR"] = "pt"
    translation_provider: Literal["deepl", "google"] = "deepl"
    deepl_api_key: Optional[str] = None

class LimitByWordsSplitterConfig(BaseConfigModel):
    type: Literal["limit_by_words"]
    limit: int

class LimitByCharsSplitterConfig(BaseConfigModel):
    type: Literal["limit_by_chars"]
    min_chars: int = 15
    max_chars: int = 30
    avoid_finishing_segment_with_word_shorter_than: int = 0

    @field_validator("min_chars", "max_chars", "avoid_finishing_segment_with_word_shorter_than")
    @classmethod
    def validate_positive_int(cls, v: int, info) -> int:
        if v < 0:
            raise ValueError(f"{info.name} must be greater than 0")
        return v
    
    @field_validator("max_chars")
    @classmethod
    def validate_max_chars(cls, v: int, info) -> int:
        min_chars = info.data.get("min_chars")
        if min_chars is not None and v < min_chars:
            raise ValueError(f"{info.name} must be greater than {min_chars}")
        return v
    
class SplitIntoSentencesSplitterConfig(BaseConfigModel):
    type: Literal["split_into_sentences"]
    sentences_separators: list[str] = ['.', '?', '!', '...']

SplitterConfig = Annotated[LimitByCharsSplitterConfig | LimitByWordsSplitterConfig | SplitIntoSentencesSplitterConfig, Field(discriminator="type")]

class EmojiInSegmentEffectConfig(BaseConfigModel):
    type: Literal["emoji_in_segment"]
    chance_to_apply: float = 0.5
    align: EmojiAlign = EmojiAlign.RANDOM
    ignore_segments_with_duration_less_than: float = 0
    max_uses_of_each_emoji: int = 2
    max_consecutive_segments_with_emoji: int = 3

class EmojiInWordEffectConfig(BaseConfigModel):
    type: Literal["emoji_in_word"]
    emojis: list[str]
    tag_condition: str = ""
    avoid_use_same_emoji_in_a_row: bool = True

class RemovePunctuationMarksEffectConfig(BaseConfigModel):
    type: Literal["remove_punctuation_marks"]
    punctuation_marks: list[str] = ['.']
    exception_marks: list[str] = ['...']

class TypewritingEffectConfig(BaseConfigModel):
    type: Literal["typewriting"]
    tag_condition: str = ""

class AnimateSegmentEmojisEffectConfig(BaseConfigModel):
    type: Literal["animate_segment_emojis"]

EffectConfig = Annotated[
    EmojiInSegmentEffectConfig |
    EmojiInWordEffectConfig |
    RemovePunctuationMarksEffectConfig |
    TypewritingEffectConfig |
    AnimateSegmentEmojisEffectConfig,
    Field(discriminator="type")]

class SoundEffectBaseConfig(BaseConfigModel):
    when: EventType
    what: ElementType
    tag_condition: str = ""
    offset: float = 0.0
    volume: float = 0.25
    interpret_consecutive_words_as_one: bool = True

class PresetSoundEffectConfig(SoundEffectBaseConfig):
    type: Literal["preset"]
    name: str

class CustomSoundEffectConfig(SoundEffectBaseConfig):
    type: Literal["custom"]
    path: str

SoundEffectConfig = Annotated[PresetSoundEffectConfig | CustomSoundEffectConfig, Field(discriminator="type")]

class BaseAnimationConfig(BaseConfigModel):
    type: Literal["fade_in", "fade_out", "zoom_in", "zoom_out", "pop_in", "pop_out", "pop_in_bounce"]
    duration: float = 0.2
    delay: float = 0.0
    when: EventType
    what: ElementType
    tag_condition: str = ""

class SlideAnimationConfig(BaseAnimationConfig):
    type: Literal["slide_in", "slide_out"]
    direction: Direction = Direction.LEFT

class BaseAnimationPrimitiveConfig(BaseConfigModel):
    type: Literal["fade_in_primitive"]
    duration: float = 0.2
    delay: float = 0.0
    transformer: Literal["linear", "ease_in", "ease_out", "ease_in_out", "inverse"] = "linear"
    what: ElementType
    when: EventType
    tag_condition: str = ""

class PopInPrimitiveAnimationConfig(BaseAnimationPrimitiveConfig):
    type: Literal["pop_in_primitive"]
    init_scale: float = 0.7
    min_scale: float = 0.3
    min_scale_at: float = 0.5
    overshoot: Optional[OvershootConfig] = None

class SlideInPrimitiveAnimationConfig(BaseAnimationPrimitiveConfig):
    type: Literal["slide_in_primitive"]
    direction: Direction = Direction.LEFT
    distance: float = 100
    overshoot: Optional[OvershootConfig] = None

class ZoomInPrimitiveAnimationConfig(BaseAnimationPrimitiveConfig):
    type: Literal["zoom_in_primitive"]
    init_scale: float = 0.5
    overshoot: Optional[OvershootConfig] = None

AnimationConfig = Annotated[
    BaseAnimationConfig |
    SlideAnimationConfig |
    BaseAnimationPrimitiveConfig |
    SlideInPrimitiveAnimationConfig |
    ZoomInPrimitiveAnimationConfig |
    PopInPrimitiveAnimationConfig,
    Field(discriminator="type")
]

class AiTaggerRuleConfig(BaseConfigModel):
    type: Literal["ai"]
    tag: str
    prompt: str

class RegexTaggerRuleConfig(BaseConfigModel):
    type: Literal["regex"]
    tag: str
    regex: str

class WordlistTaggerRuleConfig(BaseConfigModel):
    type: Literal["wordlist"]
    tag: str
    filename: str

TaggerRule = Annotated[AiTaggerRuleConfig | RegexTaggerRuleConfig | WordlistTaggerRuleConfig, Field(discriminator="type")]

class JsonSchema(BaseConfigModel):
    input: Optional[str] = None
    output: Optional[str] = None
    resources: Optional[str] = None
    css: Optional[str] = None
    video: Optional[VideoConfig] = None
    whisper: Optional[WhisperConfig] = None
    faster_whisper: Optional[FasterWhisperConfig] = None
    translation: Optional[TranslationConfig] = None
    portuguese_translation: Optional[PortugueseTranslationConfig] = None
    layout: Optional[SubtitleLayoutOptions] = None
    splitters: list[SplitterConfig] = []
    effects: list[EffectConfig] = []
    sound_effects: list[SoundEffectConfig] = []
    animations: list[AnimationConfig] = []
    tagger_rules: list[TaggerRule] = []
    cache_strategy: Optional[CacheStrategy] = None
