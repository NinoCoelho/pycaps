import typer
from typing import Optional
from pycaps.logger import set_logging_level
import logging
from pycaps.pipeline import JsonConfigLoader
from pycaps.common import VideoQuality
from pycaps.layout import VerticalAlignmentType, SubtitleLayoutOptions
from pycaps.template import TemplateLoader, DEFAULT_TEMPLATE_NAME, TemplateFactory

render_app = typer.Typer()

def _parse_styles(styles: list[str]) -> str:
    parsed_styles = {}
    for style in styles:
        selector, value = style.split(".")
        if not selector.startswith("."):
            selector = f".{selector}".strip()
        property, value = value.split("=")
        if selector not in parsed_styles:
            parsed_styles[selector] = "\n"
        parsed_styles[selector] += f"{property.strip()}: {value.strip()};\n"

    return "\n".join([f"{selector} {{ {styles} }}" for selector, styles in parsed_styles.items()])

def _parse_preview(preview: bool, preview_time: Optional[str]) -> Optional[tuple[float, float]]:
    if not preview and not preview_time:
        return None
    final_preview = tuple(map(float, preview_time.split(","))) if preview_time else (0, 5)
    if len(final_preview) != 2 or final_preview[0] < 0 or final_preview[1] < 0 or final_preview[0] >= final_preview[1]:
        typer.echo(f"Invalid preview time: {final_preview}, example: --preview-time=10,15", err=True)
        return None
    return final_preview

def _build_layout_options(builder, align, offset) -> SubtitleLayoutOptions:
    original_layout = builder._caps_pipeline._layout_options # TODO: fix this
    original_vertical_align = original_layout.vertical_align
    new_vertical_align = original_vertical_align.model_copy(update={
        "align": align or original_vertical_align.align,
        "offset": offset or 0
    })
    return original_layout.model_copy(update={"vertical_align": new_vertical_align})

@render_app.command("render", help="Render a video with subtitles using templates or custom configs. Supports Whisper transcription, styles override, layouts, and preview modes.")
def render(
    input: str = typer.Option(..., "--input", help="Input video file name", rich_help_panel="Main options", show_default=False),
    output: Optional[str] = typer.Option(None, "--output", help="Output video file name", rich_help_panel="Main options", show_default=False),
    template_name: Optional[str] = typer.Option(None, "--template", help="Template name. If no template and no config file is provided, the default template will be used", rich_help_panel="Main options", show_default=False),
    config_file: Optional[str] = typer.Option(None, "--config", help="Config JSON file path", rich_help_panel="Main options", show_default=False),
    transcription_preview: bool = typer.Option(False, "--transcription-preview", help="Stops the rendering process and shows an editable preview of the transcription", rich_help_panel="Main options", show_default=False),

    layout_align: Optional[VerticalAlignmentType] = typer.Option(None, "--layout-align", help="Vertical alignment for subtitles", rich_help_panel="Layout", show_default=False),
    layout_align_offset: Optional[float] = typer.Option(None, "--layout-align-offset", help="Vertical alignment offset. Positive values move the subtitles down, negative values move them up", rich_help_panel="Layout", show_default=False),

    style: list[str] = typer.Option(None, "--style", help="Override styles of the template, example: --style word.color=red", rich_help_panel="Style", show_default=False),

    language: Optional[str] = typer.Option(None, "--lang", help="Language of the video, example: --lang=en", rich_help_panel="Whisper", show_default=False),
    whisper_model: Optional[str] = typer.Option(None, "--whisper-model", help="Whisper model to use, example: --whisper-model=medium", rich_help_panel="Whisper", show_default=False),
    initial_prompt: Optional[str] = typer.Option(None, "--initial-prompt", help="Custom prompt to guide Whisper transcription", rich_help_panel="Whisper", show_default=False),
    portuguese_vocab: list[str] = typer.Option([], "--pt-vocab", help="Additional Portuguese vocabulary terms (can be used multiple times)", rich_help_panel="Whisper"),
    transcription_quality: Optional[str] = typer.Option(None, "--transcription-quality", help="Anti-hallucination preset: maximum_quality, balanced, fast_processing, podcasts, short_videos", rich_help_panel="Whisper", show_default=False),
    use_faster_whisper: bool = typer.Option(False, "--faster-whisper", help="Use faster-whisper (4x faster, less hallucinations)", rich_help_panel="Whisper", show_default=False),
    disable_vad: bool = typer.Option(False, "--disable-vad", help="Disable VAD (Voice Activity Detection) - useful for music videos to capture all words", rich_help_panel="Whisper", show_default=False),
    hallucination_silence_threshold: Optional[float] = typer.Option(None, "--hallucination-threshold", help="Silence threshold to prevent hallucinations (seconds). Lower = more aggressive. Default: 2.0", rich_help_panel="Whisper", show_default=False),

    # Translation options
    translate: Optional[str] = typer.Option(None, "--translate", help="Enable translation from source to target language (e.g., en-pt, en-pt-BR)", rich_help_panel="Translation", show_default=False),
    translation_provider: Optional[str] = typer.Option("deepl", "--translation-provider", help="Translation service: deepl (higher quality) or google (free)", rich_help_panel="Translation", show_default=False),
    deepl_api_key: Optional[str] = typer.Option(None, "--deepl-api-key", help="DeepL API key (optional, can use DEEPL_API_KEY env var)", rich_help_panel="Translation", show_default=False),
    portuguese_variant: Optional[str] = typer.Option("pt", "--portuguese-variant", help="Portuguese variant: pt (European) or pt-BR (Brazilian)", rich_help_panel="Translation", show_default=False),
    enable_context_translation: bool = typer.Option(True, "--context-translation/--no-context-translation", help="Enable context-aware batch translation", rich_help_panel="Translation", show_default=False),

    # AI Enhancement options
    ai_enhancements: bool = typer.Option(True, "--ai-enhancements/--no-ai-enhancements", help="Enable AI-powered word highlighting and emoji enhancements", rich_help_panel="AI Enhancement", show_default=False),
    ai_preset: Optional[str] = typer.Option(None, "--ai-preset", help="AI enhancement preset: minimal, balanced, aggressive, professional, entertainment", rich_help_panel="AI Enhancement", show_default=False),
    ai_word_highlighting: bool = typer.Option(True, "--ai-word-highlighting/--no-ai-word-highlighting", help="Enable AI-powered word importance detection and highlighting", rich_help_panel="AI Enhancement", show_default=False),
    ai_emoji_enhancement: bool = typer.Option(True, "--ai-emoji-enhancement/--no-ai-emoji-enhancement", help="Enable AI-powered emoji suggestions", rich_help_panel="AI Enhancement", show_default=False),
    ai_content_type: Optional[str] = typer.Option("general", "--ai-content-type", help="Content type for AI analysis: general, educational, professional, entertainment", rich_help_panel="AI Enhancement", show_default=False),

    video_quality: Optional[VideoQuality] = typer.Option(None, "--video-quality", help="Final video quality", rich_help_panel="Video", show_default=False),

    preview: bool = typer.Option(False, "--preview", help="Generate a low quality preview of the rendered video", rich_help_panel="Utils"),
    preview_time: Optional[str] = typer.Option(None, "--preview-time", help="Generate a low quality preview of the rendered video at the given time, example: --preview-time=10,15", rich_help_panel="Utils", show_default=False),
    subtitle_data: Optional[str] = typer.Option(None, "--subtitle-data", help="Subtitle data file path. If provided, the rendering process will skip the transcription and tagging steps", rich_help_panel="Utils", show_default=False),
    srt_file: Optional[str] = typer.Option(None, "--srt-file", help="SRT subtitle file to import (skips transcription). Example: --srt-file=subtitles.srt", rich_help_panel="Utils", show_default=False),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose mode", rich_help_panel="Utils"),
):
    set_logging_level(logging.DEBUG if verbose else logging.INFO)
    
    # Validation: ensure only one input method is used
    input_methods = [bool(template_name), bool(config_file)]
    if sum(input_methods) > 1:
        typer.echo("Only one of --template or --config can be provided", err=True)
        return None
    
    # Validation: ensure only one subtitle source is used
    subtitle_sources = [bool(subtitle_data), bool(srt_file)]
    if sum(subtitle_sources) > 1:
        typer.echo("Only one of --subtitle-data or --srt-file can be provided", err=True)
        return None
    
    if not template_name and not config_file:
        template_name = DEFAULT_TEMPLATE_NAME
    
    if template_name:
        typer.echo(f"Rendering {input} with template {template_name}...")
        template = TemplateFactory().create(template_name)
        builder = TemplateLoader(template).with_input_video(input).load(False)
    elif config_file:
        typer.echo(f"Rendering {input} with config file {config_file}...")
        builder = JsonConfigLoader(config_file).load(False)
        
    if output: builder.with_output_video(output)
    if style: builder.add_css_content(_parse_styles(style))
    
    # Handle translation configuration
    if translate:
        # Parse translation languages (e.g., "en-pt" or "en-pt-BR")
        if "-" in translate:
            source_lang, target_lang = translate.split("-", 1)
        else:
            typer.echo("Invalid translation format. Use format like: en-pt or en-pt-BR", err=True)
            return None
        
        # For Portuguese translations, use the convenience method
        if target_lang.startswith("pt"):
            typer.echo(f"Configuring English-to-Portuguese translation ({target_lang})...")
            typer.echo(f"Using {translation_provider} translation service")
            
            builder.with_portuguese_translation(
                transcriber_type="faster_whisper" if use_faster_whisper else "whisper",
                model_size=whisper_model if whisper_model else "base",
                variant=target_lang,
                translation_provider=translation_provider,
                deepl_api_key=deepl_api_key
            )
        else:
            # Generic translation
            typer.echo(f"Configuring translation: {source_lang} -> {target_lang}")
            
            builder.with_translation(
                source_language=source_lang,
                target_language=target_lang,
                transcriber_type="faster_whisper" if use_faster_whisper else "whisper", 
                model_size=whisper_model if whisper_model else "base",
                translation_provider=translation_provider,
                deepl_api_key=deepl_api_key,
                enable_context_translation=enable_context_translation
            )
    
    # Regular transcription (only if not using translation)
    elif use_faster_whisper:
        threshold = hallucination_silence_threshold if hallucination_silence_threshold is not None else (2.0 if not disable_vad else None)
        if disable_vad:
            typer.echo("Using faster-whisper with VAD DISABLED (for music videos)...")
        else:
            typer.echo("Using faster-whisper for transcription (4x faster, less hallucinations)...")
        builder.with_faster_whisper(
            model_size=whisper_model if whisper_model else "base",
            language=language,
            use_vad=not disable_vad,
            hallucination_silence_threshold=threshold
        )
    # TODO: this has a little issue (if you set lang via js + whisper model by cli, it will change the lang to None)
    elif language or whisper_model or initial_prompt or portuguese_vocab or transcription_quality: 
        builder.with_whisper_config(
            language=language, 
            model_size=whisper_model if whisper_model else "medium",
            initial_prompt=initial_prompt,
            portuguese_vocabulary=portuguese_vocab if portuguese_vocab else None,
            anti_hallucination_config=transcription_quality if transcription_quality else "balanced"
        )
    if subtitle_data: builder.with_subtitle_data_path(subtitle_data)
    if srt_file: 
        typer.echo(f"Using SRT file: {srt_file}")
        builder.with_srt_file(srt_file)
    if transcription_preview: builder.should_preview_transcription(True)
    if video_quality: builder.with_video_quality(video_quality)
    if layout_align or layout_align_offset: builder.with_layout_options(_build_layout_options(builder, layout_align, layout_align_offset))
    
    # Configure AI enhancements
    if ai_enhancements:
        typer.echo(f"Enabling AI enhancements (preset: {ai_preset or 'custom'})...")
        builder.with_ai_enhancements(
            enabled=True,
            preset=ai_preset,
            word_highlighting=ai_word_highlighting,
            emoji_enhancement=ai_emoji_enhancement,
            content_type=ai_content_type,
            template_name=template_name
        )
        
        # Set specific configurations
        if not ai_word_highlighting:
            builder.with_ai_word_highlighting(enabled=False)
        if not ai_emoji_enhancement:
            builder.with_ai_emoji_enhancement(enabled=False)

    pipeline = builder.build(preview_time=_parse_preview(preview, preview_time))
    pipeline.run()
