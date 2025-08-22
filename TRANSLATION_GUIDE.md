# English-to-Portuguese Translation Guide

This guide explains how to use pycaps for high-precision English-to-Portuguese video subtitle translation, implementing the enhanced specification from `english-portuguese-enhancement.md`.

## Features

- **Professional Translation Services**: DeepL (recommended) and Google Translate support
- **Faster-Whisper Integration**: 4x faster transcription with built-in anti-hallucination
- **Portuguese-Specific Optimization**: Optimized line lengths, reading speeds, and formatting
- **Context-Aware Translation**: Batch processing for better translation quality
- **Comprehensive Quality Validation**: Detailed metrics and quality scoring
- **Multiple Input Sources**: Audio transcription or SRT file import

## Quick Start

### CLI Usage

#### Basic English-to-Portuguese Translation
```bash
# Brazilian Portuguese with DeepL (recommended)
pycaps render input.mp4 output.mp4 --translate en-pt-BR --translation-provider deepl

# European Portuguese with Google Translate (free)
pycaps render input.mp4 output.mp4 --translate en-pt --translation-provider google

# With custom Whisper model and DeepL API key
pycaps render input.mp4 output.mp4 \
  --translate en-pt-BR \
  --translation-provider deepl \
  --deepl-api-key "your-api-key" \
  --whisper-model medium \
  --faster-whisper
```

#### Advanced Options
```bash
pycaps render input.mp4 output.mp4 \
  --translate en-pt-BR \
  --translation-provider deepl \
  --deepl-api-key "your-key" \
  --template hype \
  --faster-whisper \
  --whisper-model base \
  --no-context-translation \
  --verbose
```

### Python API Usage

#### Simple Translation
```python
from pycaps.pipeline import CapsPipelineBuilder

# Basic Portuguese translation
pipeline = (CapsPipelineBuilder()
    .with_input_video("english_video.mp4")
    .with_portuguese_translation(
        variant="pt-BR",
        translation_provider="deepl",
        deepl_api_key="your-api-key"
    )
    .with_output_video("portuguese_subtitles.mp4")
    .build())

result = pipeline.run()
```

#### Advanced Translation Configuration
```python
from pycaps.pipeline import CapsPipelineBuilder

# Custom translation settings
pipeline = (CapsPipelineBuilder()
    .with_input_video("video.mp4")
    .with_translation(
        source_language="en",
        target_language="pt-BR",
        transcriber_type="faster_whisper",  # 4x faster
        model_size="medium",
        translation_provider="deepl",
        deepl_api_key="your-key",
        max_line_length=42,  # Netflix standard
        reading_speed=17,    # Brazilian Portuguese
        enable_context_translation=True
    )
    .with_template("hype")
    .with_output_video("result.mp4")
    .build())

result = pipeline.run()
```

### JSON Configuration

Create a configuration file `config.json`:

```json
{
  "input": "english_video.mp4",
  "output": "portuguese_subtitles.mp4",
  "translation": {
    "source_language": "en",
    "target_language": "pt-BR",
    "transcriber_type": "faster_whisper",
    "model_size": "base", 
    "translation_provider": "deepl",
    "max_line_length": 42,
    "reading_speed": 17,
    "enable_context_translation": true
  }
}
```

Then run:
```bash
pycaps render --config config.json
```

## Configuration Options

### Translation Settings

| Option | Default | Description |
|--------|---------|-------------|
| `source_language` | `"en"` | Source language code |
| `target_language` | `"pt"` | Target language (`"pt"` or `"pt-BR"`) |
| `transcriber_type` | `"faster_whisper"` | Transcriber (`"whisper"` or `"faster_whisper"`) |
| `model_size` | `"base"` | Whisper model size |
| `translation_provider` | `"deepl"` | Translation service (`"deepl"` or `"google"`) |
| `deepl_api_key` | `None` | DeepL API key (can use env var `DEEPL_API_KEY`) |
| `max_line_length` | `42` | Maximum characters per line |
| `reading_speed` | `17` | Maximum chars per second |
| `enable_context_translation` | `true` | Use batch translation for context |

### Portuguese-Specific Defaults

| Variant | Max Line Length | Reading Speed | Notes |
|---------|----------------|---------------|-------|
| `pt` | 40 chars | 18 cps | European Portuguese |
| `pt-BR` | 42 chars | 17 cps | Brazilian Portuguese (Netflix standard) |

## Translation Services

### DeepL (Recommended)
- **Pros**: Higher translation quality, better context understanding
- **Cons**: Requires API key, usage limits
- **Setup**: Get API key from [DeepL](https://www.deepl.com/pro-api)
- **Env Var**: `DEEPL_API_KEY=your-api-key`

### Google Translate
- **Pros**: Free, no API key required
- **Cons**: Lower quality, rate limits
- **Setup**: No setup required
- **Usage**: Automatic fallback if DeepL unavailable

## Quality Validation

The system automatically validates translation quality:

### Quality Metrics
- **Reading Speed**: Ensures subtitles are readable within time limits
- **Line Length**: Validates text fits within display constraints  
- **Duration**: Checks minimum/maximum subtitle display times
- **Translation Quality**: Detects suspicious or empty translations
- **Timing**: Validates no overlaps or excessive gaps

### Quality Scores
- **0.9-1.0**: Excellent - Ready for production
- **0.8-0.9**: Good - Minor improvements possible
- **0.6-0.8**: Moderate - Several issues need attention
- **0.0-0.6**: Poor - Significant issues require fixing

### Quality Reports
Enable detailed reporting with verbose logging:

```bash
pycaps render input.mp4 output.mp4 --translate en-pt-BR --verbose
```

## Performance Optimization

### For Speed (Recommended)
```python
pipeline = (CapsPipelineBuilder()
    .with_portuguese_translation(
        transcriber_type="faster_whisper",  # 4x faster
        model_size="base",                  # Faster model
        translation_provider="google"       # No API delays
    ))
```

### For Quality
```python  
pipeline = (CapsPipelineBuilder()
    .with_portuguese_translation(
        transcriber_type="whisper",         # Higher accuracy
        model_size="large-v3",             # Best model
        translation_provider="deepl"       # Better translations
    ))
```

### For Large Files
```python
pipeline = (CapsPipelineBuilder()
    .with_translation(
        transcriber_type="faster_whisper",
        model_size="base",
        enable_context_translation=False,  # Disable batching
        batch_size=3                       # Smaller batches
    ))
```

## Troubleshooting

### Common Issues

1. **DeepL API Key Not Working**
   ```bash
   export DEEPL_API_KEY="your-actual-api-key"
   # or use --deepl-api-key flag
   ```

2. **Poor Translation Quality**
   - Try DeepL instead of Google Translate
   - Enable context translation: `--context-translation`
   - Use larger Whisper model: `--whisper-model medium`

3. **Slow Processing**
   - Use faster-whisper: `--faster-whisper`
   - Use smaller model: `--whisper-model base`
   - Disable context translation: `--no-context-translation`

4. **Reading Speed Issues**
   - Adjust reading speed: Configure `reading_speed` in JSON
   - Increase max duration: Configure `max_duration`
   - Decrease line length: Configure `max_line_length`

### Error Messages

- **"TranslationServiceUnavailable"**: Check API key and internet connection
- **"Invalid translation format"**: Use format like `en-pt` or `en-pt-BR`
- **"No translation service available"**: Install dependencies: `pip install deep-translator`

## Examples

### 1. YouTube Video to Brazilian Portuguese
```bash
pycaps render youtube_video.mp4 br_subtitles.mp4 \
  --translate en-pt-BR \
  --translation-provider deepl \
  --template hype \
  --faster-whisper
```

### 2. Podcast to European Portuguese  
```bash
pycaps render podcast.mp4 pt_podcast.mp4 \
  --translate en-pt \
  --translation-provider google \
  --whisper-model medium \
  --transcription-quality podcasts
```

### 3. Educational Content
```bash
pycaps render lecture.mp4 aula.mp4 \
  --translate en-pt-BR \
  --translation-provider deepl \
  --template minimal \
  --whisper-model large-v3
```

## Integration with Existing Workflows

### With SRT Files
```bash
# First generate SRT, then translate
pycaps render video.mp4 temp.mp4 --srt-file english.srt
# Then use translation
pycaps render video.mp4 final.mp4 --translate en-pt-BR --srt-file english.srt
```

### Batch Processing
```python
import os
from pycaps.pipeline import CapsPipelineBuilder

def translate_videos(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.mp4'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"pt_{filename}")
            
            pipeline = (CapsPipelineBuilder()
                .with_input_video(input_path)
                .with_portuguese_translation()
                .with_output_video(output_path)
                .build())
            
            pipeline.run()
```

## Contributing

To improve translation quality:

1. **Test with different content types**: Videos, podcasts, lectures
2. **Validate Portuguese variants**: European vs Brazilian
3. **Optimize reading speeds**: Test with native speakers
4. **Improve quality metrics**: Add domain-specific validations
5. **Enhance context handling**: Better semantic batching

For issues or suggestions, please see the main project repository.