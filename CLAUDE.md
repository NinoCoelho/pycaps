# pycaps - Claude Context

**Project Type:** Python Library & CLI Tool
**Primary Technologies:** Python 3.10+, Whisper AI, Playwright, FFmpeg, OpenCV
**Domain:** Video Subtitle Generation with CSS Styling
**Last Updated:** 2025-08-21

## Project Overview

pycaps is a sophisticated Python library for adding dynamic, CSS-styled subtitles to videos. It's designed for creating engaging short-form video content for platforms like TikTok, YouTube Shorts, and Instagram Reels. The project combines AI transcription, advanced text rendering, and powerful animation capabilities.

### Key Capabilities
- **Advanced anti-hallucination Whisper transcription** with VAD preprocessing and chunking
- Automatic speech-to-text transcription with word-level timestamps
- **SRT file import with intelligent word-level timing estimation**
- CSS-based subtitle rendering with browser-quality typography
- Hierarchical animation system with primitives and presets
- Smart content targeting through semantic and structural tagging
- Template-based styling with 12 built-in templates
- CLI and programmatic Python API interfaces
- **Duration-based adaptive configuration** for optimal transcription quality

## Architecture Overview

### Data Hierarchy
The system follows a hierarchical data model:
```
Document → Segment → Line → Word → WordClip
```
- **Document**: Complete subtitle project
- **Segment**: Logical grouping of content (sentence/phrase)
- **Line**: Visual text line in rendered output
- **Word**: Individual word with timing and styling
- **WordClip**: Rendered word image with metadata

### Processing Pipeline
1. **Transcription**: Audio → Text with timestamps *OR* SRT → Document structure
2. **Segmentation**: Text → Logical segments
3. **Tagging**: Apply semantic/structural tags
4. **Selection**: Target specific content
5. **Styling**: Apply CSS and effects
6. **Animation**: Add entrance/exit animations
7. **Rendering**: Generate styled images
8. **Composition**: Combine with video

## Module Structure

### Core Modules
- **`src/pycaps/pipeline/`** - Central orchestration ([See module CLAUDE.md](src/pycaps/pipeline/CLAUDE.md))
- **`src/pycaps/renderer/`** - CSS rendering engine ([See module CLAUDE.md](src/pycaps/renderer/CLAUDE.md))
- **`src/pycaps/transcriber/`** - Audio transcription ([See module CLAUDE.md](src/pycaps/transcriber/CLAUDE.md))
- **`src/pycaps/animation/`** - Animation framework ([See module CLAUDE.md](src/pycaps/animation/CLAUDE.md))
- **`src/pycaps/template/`** - Template system ([See module CLAUDE.md](src/pycaps/template/CLAUDE.md))

### Supporting Modules
- **`src/pycaps/tag/`** - Content tagging system
- **`src/pycaps/selector/`** - Content selection engine
- **`src/pycaps/effect/`** - Text and clip effects
- **`src/pycaps/layout/`** - Text layout engine
- **`src/pycaps/video/`** - Video composition
- **`src/pycaps/cli/`** - Command-line interface
- **`src/pycaps/ai/`** - LLM integration

## Development Setup

### Installation
```bash
# From source (development)
pip install -e .

# From PyPI
pip install pycaps
```

### Dependencies
- **Core**: Python 3.10+, setuptools
- **Transcription**: openai-whisper, google-cloud-speech, librosa, soundfile, torch
- **Anti-hallucination**: silero-vad (via torch.hub), numpy
- **Rendering**: playwright, pillow
- **Video**: opencv-python, ffmpeg-python, pydub
- **CLI**: typer, rich
- **Data**: pydantic, numpy

### Environment Variables
- `PYCAPS_AI_ENABLED` - Enable/disable AI functionality (optional, defaults to "true", set to "false"/"0"/"no"/"off" to disable)
- `OPENAI_API_KEY` - For AI-powered features (tagging, summarization) - required for AI functionality
- `OPENAI_BASE_URL` - Custom API endpoint (optional, for OpenRouter or other OpenAI-compatible APIs)
- `PYCAPS_AI_MODEL` - AI model to use (optional, defaults to "gpt-4o-mini")
- `GOOGLE_APPLICATION_CREDENTIALS` - For Google Speech API (optional)

## Usage Patterns

### CLI Usage
```bash
# Basic rendering
pycaps render video.mp4 output.mp4

# With template
pycaps render video.mp4 output.mp4 --template hype

# Custom configuration
pycaps render video.mp4 output.mp4 --config config.json

# With SRT file (bypasses audio transcription)
pycaps render video.mp4 output.mp4 --srt-file subtitles.srt --template hype

# Advanced transcription for long videos (anti-hallucination)
pycaps render long_video.mp4 output.mp4 --transcription-quality maximum_quality

# Podcast-optimized transcription
pycaps render podcast.mp4 output.mp4 --transcription-quality podcasts
```

### Python API
```python
from pycaps import CapsPipeline
from pycaps.transcriber import WhisperAudioTranscriber

# Basic usage
pipeline = CapsPipeline()
pipeline.process("input.mp4", "output.mp4")

# With advanced anti-hallucination transcription
transcriber = WhisperAudioTranscriber(
    model_size="medium",
    anti_hallucination_config="maximum_quality"
)
pipeline = CapsPipeline(transcriber=transcriber)
pipeline.process("long_video.mp4", "output.mp4")

# Preset configurations for different content types
transcriber = WhisperAudioTranscriber(
    model_size="large-v2",
    anti_hallucination_config="podcasts"  # or "short_videos", "balanced"
)
```

## Configuration System

### JSON Configuration Structure
```json
{
  "transcriber": {...},
  "template": {...},
  "tags": [...],
  "selectors": [...],
  "effects": [...],
  "animations": {...}
}
```

### Key Configuration Files
- `src/pycaps/config/default_config.json` - Base configuration
- `src/pycaps/template/templates/*/template.json` - Template configs
- User configs can override any settings

## Testing & Quality

### Current Status
- **Testing Infrastructure**: Not yet implemented (critical gap)
- **Code Style**: Modern Python with type hints
- **Documentation**: Comprehensive markdown docs in `/docs/`

### Recommended Testing Setup
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run tests (when implemented)
pytest tests/
```

## Common Development Tasks

### Adding a New Template
1. Create directory: `src/pycaps/template/templates/[name]/`
2. Add `template.json` configuration
3. Include CSS files and resources
4. Register in template loader

### Creating Custom Animations
1. Extend `PrimitiveAnimation` or `PresetAnimation`
2. Implement `apply()` method
3. Register in animation registry
4. Use in configuration or code

### Implementing New Effects
1. Create class extending appropriate effect base
2. Implement effect logic
3. Register in effect system
4. Configure in JSON or code

## Performance Considerations

### Bottlenecks
- **Rendering**: Browser-based rendering can be slow
- **Transcription**: Whisper models vary in speed/accuracy
- **Video Processing**: Large videos require significant memory

### Optimization Strategies
- Use caching for rendered images
- Choose appropriate Whisper model size
- Process in chunks for large videos
- Leverage multiprocessing where possible

## Debugging Tips

### Common Issues
1. **Playwright not installed**: Run `playwright install`
2. **FFmpeg missing**: Install system FFmpeg
3. **Memory errors**: Reduce batch size or video resolution
4. **Transcription failures**: Check audio quality and format
5. **Whisper hallucinations**: Use anti-hallucination configs for videos >90s
6. **VAD model download**: Silero VAD downloads automatically via torch.hub

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Architecture Decisions

### Why Browser-Based Rendering?
- Perfect CSS compliance
- Advanced typography support
- Complex animation capabilities
- Cross-platform consistency

### Why Hierarchical Data Model?
- Granular styling control
- Efficient animation targeting
- Natural content organization
- Flexible selection mechanisms

## Related Documentation

### Internal Docs
- [API Usage Guide](docs/API_USAGE.md)
- [CLI Reference](docs/CLI.md)
- [Configuration Reference](docs/CONFIG_REFERENCE.md)
- [Core Structure](docs/CORE_STRUCTURE.md)
- [Examples](docs/EXAMPLES.md)
- [Tags Documentation](docs/TAGS.md)
- [Templates Guide](docs/TEMPLATES.md)

### External Resources
- [Whisper Documentation](https://github.com/openai/whisper)
- [Playwright Python](https://playwright.dev/python/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

## Project Roadmap

### Current Version: 0.2.0 (Alpha)

### New in v0.2.0
- **Anti-hallucination transcription system** for long videos (>90s)
- **VAD (Voice Activity Detection)** preprocessing with Silero VAD
- **Enhanced chunking strategy** with overlapping segments
- **Advanced post-processing filters** (compression ratio, semantic similarity, looping detection)
- **Model selection optimization** with automatic fallbacks
- **Duration-based adaptive configuration** 
- **Preset configurations** for different content types
- **Improved dependencies** (librosa, soundfile, torch)

### Planned Features
- Test suite implementation
- Performance optimizations
- Additional AI providers
- More built-in templates
- Advanced effect system
- Real-time preview improvements
- WebRTC real-time transcription
- GPU acceleration optimizations

## Contributing Guidelines

### Code Style
- Use type hints for all functions
- Follow PEP 8 conventions
- Document complex logic
- Maintain module separation

### Pull Request Process
1. Create feature branch
2. Implement with documentation
3. Add tests (when framework exists)
4. Update relevant CLAUDE.md files
5. Submit PR with clear description

---
*pycaps v0.2.0 | CSS-styled video subtitles | Anti-hallucination AI transcription | Modular architecture*