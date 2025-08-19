# Pipeline Module - Claude Context

**Module Type:** Core Processing Orchestration
**Primary Technologies:** Python, Pydantic, Multiprocessing, JSON Configuration
**Dependencies:** All pycaps modules (transcriber, renderer, animation, etc.)
**Last Updated:** 2025-08-19

## Module Overview

The Pipeline module is the central orchestration system for pycaps. It coordinates the entire video subtitle generation workflow, from audio transcription or SRT import through final video composition. The module implements a flexible builder pattern that allows for both programmatic and configuration-driven pipeline construction with support for multiple input sources.

### Core Responsibilities
- Workflow orchestration across all pycaps modules
- Configuration loading and validation
- State management during processing
- Error handling and recovery
- Progress tracking and reporting
- Resource management and cleanup

## Architecture & Design Patterns

### Builder Pattern Implementation
The module uses a sophisticated builder pattern to construct processing pipelines:

```
CapsPipelineBuilder → CapsPipeline
```

- **CapsPipelineBuilder**: Fluent interface for pipeline configuration
- **CapsPipeline**: Immutable processing pipeline with configured components

### Processing Workflow
```
Audio/Video Input → Transcription → Segmentation → Tagging → Selection → 
Styling → Animation → Rendering → Composition → Output Video
```

## Key Components

### 1. CapsPipeline (`caps_pipeline.py`)

**Purpose**: Main processing orchestrator
**Key Methods**:
- `process(input_file, output_file)` - Execute complete pipeline
- `process_with_config(config)` - Process with configuration object
- `get_intermediate_results()` - Access pipeline state

**Processing Stages**:
1. **Input Validation** - Verify file formats and accessibility
2. **Transcription** - Extract speech with word-level timestamps
3. **Document Creation** - Build hierarchical data structure
4. **Content Processing** - Apply tags, selectors, effects
5. **Rendering** - Generate styled subtitle images
6. **Composition** - Combine with source video
7. **Output Generation** - Write final video file

### 2. CapsPipelineBuilder (`caps_pipeline_builder.py`)

**Purpose**: Fluent interface for pipeline configuration
**Key Methods**:
```python
builder = CapsPipelineBuilder()
pipeline = (builder
    .with_transcriber(transcriber_config)
    .with_template(template_name)
    .with_effects(effects_list)
    .with_animations(animation_config)
    .build())
```

**Configuration Categories**:
- **Transcriber Settings** - Model selection, language, quality
- **SRT Import** - Subtitle file import with intelligent timing
- **Template Configuration** - Styling templates and overrides
- **Effect Chains** - Text and clip effects to apply
- **Animation Sequences** - Entrance/exit animations
- **Rendering Options** - Quality, caching, performance
- **Output Settings** - Format, resolution, codec

### 3. JSON Configuration Loader (`json_config_loader.py`)

**Purpose**: Load and validate JSON configuration files
**Supported Formats**:
```json
{
  "transcriber": {
    "provider": "whisper",
    "model": "base",
    "language": "auto"
  },
  "template": {
    "name": "hype",
    "overrides": {...}
  },
  "tags": [...],
  "selectors": [...],
  "effects": [...],
  "animations": {...},
  "rendering": {...},
  "output": {...}
}
```

**Validation Features**:
- Schema validation with Pydantic models
- Required/optional field checking
- Type coercion and defaults
- Configuration inheritance and merging

## Data Flow Architecture

### Input Processing
```python
# File inputs
input_video = "path/to/video.mp4"
config = "config.json" or config_dict

# Pipeline creation
pipeline = CapsPipeline.from_config(config)
result = pipeline.process(input_video, "output.mp4")
```

### Intermediate Data Structures
- **TranscriptionResult** - Raw transcription with timestamps
- **Document** - Hierarchical subtitle structure
- **ProcessingContext** - Shared state and metadata
- **RenderingPlan** - Instructions for visual generation
- **CompositionSpec** - Final video assembly requirements

### State Management
The pipeline maintains processing state through:
- **Context Objects** - Shared data across processing stages
- **Progress Tracking** - Real-time progress reporting
- **Error Context** - Detailed error information with recovery options
- **Resource Tracking** - Memory and file handle management

## Configuration System

### Configuration Hierarchy
1. **Default Configuration** - Built-in sensible defaults
2. **Template Configuration** - Template-specific settings
3. **User Configuration** - Custom JSON configuration files
4. **Runtime Overrides** - Programmatic parameter overrides

### Configuration Validation
```python
from pydantic import BaseModel

class PipelineConfig(BaseModel):
    transcriber: TranscriberConfig
    template: TemplateConfig
    tags: List[TagConfig] = []
    selectors: List[SelectorConfig] = []
    effects: List[EffectConfig] = []
    animations: AnimationConfig
    rendering: RenderingConfig
    output: OutputConfig
```

### Environment Integration
- **Environment Variables** - API keys, paths, performance settings
- **System Detection** - GPU availability, memory limits
- **Platform Optimization** - OS-specific optimizations

## Error Handling & Recovery

### Error Categories
1. **Input Errors** - Invalid files, unsupported formats
2. **Processing Errors** - Transcription failures, rendering issues
3. **Resource Errors** - Memory limits, disk space
4. **Configuration Errors** - Invalid settings, missing dependencies

### Recovery Strategies
```python
try:
    result = pipeline.process(input_file, output_file)
except TranscriptionError as e:
    # Fallback to alternative transcriber
    pipeline = pipeline.with_fallback_transcriber()
    result = pipeline.process(input_file, output_file)
except RenderingError as e:
    # Reduce quality settings
    pipeline = pipeline.with_reduced_quality()
    result = pipeline.process(input_file, output_file)
```

### Logging & Monitoring
- **Structured Logging** - JSON-formatted logs with context
- **Performance Metrics** - Timing and resource usage
- **Progress Callbacks** - Real-time status updates
- **Debug Information** - Detailed tracing for troubleshooting

## Performance Optimization

### Parallel Processing
```python
# Multi-stage pipeline with concurrent execution
pipeline = (CapsPipelineBuilder()
    .with_parallel_transcription()
    .with_concurrent_rendering()
    .with_streaming_composition()
    .build())
```

### Caching Strategies
- **Transcription Cache** - Reuse transcriptions for identical audio
- **Rendering Cache** - Cache styled text images
- **Template Cache** - Precompiled CSS and resources
- **Configuration Cache** - Parsed and validated configurations

### Memory Management
- **Streaming Processing** - Process large videos in chunks
- **Resource Cleanup** - Automatic cleanup of temporary resources
- **Memory Monitoring** - Track and limit memory usage
- **Garbage Collection** - Explicit cleanup of heavy objects

## Integration Points

### Module Dependencies
```python
# Required modules
from ..transcriber import create_transcriber
from ..renderer import CSSRenderer
from ..animation import AnimationEngine
from ..template import TemplateLoader
from ..video import VideoComposer
```

### External Dependencies
- **FFmpeg** - Video processing and composition
- **Whisper** - Speech-to-text transcription
- **Playwright** - CSS rendering browser automation
- **OpenCV** - Video frame processing
- **Pydub** - Audio processing

## Development Workflows

### Pipeline Testing
```python
# Create test pipeline
test_pipeline = (CapsPipelineBuilder()
    .with_mock_transcriber()
    .with_test_template()
    .with_validation_mode()
    .build())

# Run with test inputs
result = test_pipeline.process("test.mp4", "output.mp4")
assert result.success
```

### Configuration Development
```python
# Load and validate config
config = load_json_config("new_config.json")
validated = PipelineConfig.parse_obj(config)

# Test pipeline creation
pipeline = CapsPipeline.from_config(validated)
```

### Custom Component Integration
```python
class CustomTranscriber(BaseTranscriber):
    def transcribe(self, audio_file):
        # Custom implementation
        pass

# Register with pipeline
pipeline = (CapsPipelineBuilder()
    .with_custom_transcriber(CustomTranscriber())
    .build())
```

## Common Use Cases

### Basic Video Processing
```python
from pycaps.pipeline import CapsPipeline

pipeline = CapsPipeline()
result = pipeline.process("input.mp4", "output.mp4")
```

### Template-Based Processing
```python
pipeline = CapsPipeline.from_template("hype")
result = pipeline.process("input.mp4", "output.mp4")
```

### Custom Configuration
```python
config = {
    "transcriber": {"model": "large", "language": "en"},
    "template": {"name": "custom", "overrides": {...}},
    "effects": [{"type": "emoji", "intensity": 0.8}]
}

pipeline = CapsPipeline.from_config(config)
result = pipeline.process("input.mp4", "output.mp4")
```

### SRT File Processing
```python
from pycaps.pipeline import CapsPipelineBuilder

# Basic SRT processing
builder = CapsPipelineBuilder()
pipeline = (builder
    .with_input_video("input.mp4")
    .with_srt_file("subtitles.srt")
    .with_template("hype")
    .build())

result = pipeline.process("input.mp4", "output.mp4")

# SRT with custom styling
pipeline = (builder
    .with_srt_file("subtitles.srt")
    .with_effects([{"type": "emoji", "intensity": 0.5}])
    .build())
```

### Batch Processing
```python
from concurrent.futures import ProcessPoolExecutor

def process_video(args):
    input_file, output_file, config = args
    pipeline = CapsPipeline.from_config(config)
    return pipeline.process(input_file, output_file)

# Process multiple videos
with ProcessPoolExecutor() as executor:
    futures = executor.map(process_video, video_batches)
    results = list(futures)
```

## Troubleshooting Guide

### Common Issues

1. **Pipeline Creation Failures**
   ```python
   # Debug configuration
   try:
       pipeline = CapsPipeline.from_config(config)
   except ValidationError as e:
       print(f"Config validation error: {e}")
   ```

2. **Processing Hangs**
   - Check transcriber model availability
   - Verify FFmpeg installation
   - Monitor memory usage
   - Enable debug logging

3. **Resource Exhaustion**
   ```python
   # Enable resource monitoring
   pipeline = (CapsPipelineBuilder()
       .with_memory_limit("4GB")
       .with_timeout(300)
       .build())
   ```

4. **Quality Issues**
   - Verify input video quality
   - Check template configuration
   - Review rendering settings
   - Test with simpler effects

### Debug Configuration
```json
{
  "debug": {
    "enable_logging": true,
    "save_intermediates": true,
    "memory_profiling": true,
    "timing_analysis": true
  }
}
```

## API Reference

### Core Classes
- **`CapsPipeline`** - Main processing pipeline
- **`CapsPipelineBuilder`** - Fluent configuration builder
- **`PipelineConfig`** - Configuration data model
- **`ProcessingResult`** - Pipeline execution result

### Key Methods
- **`CapsPipeline.process(input, output)`** - Execute pipeline
- **`CapsPipelineBuilder.build()`** - Create configured pipeline
- **`load_json_config(path)`** - Load configuration file
- **`validate_config(config)`** - Validate configuration

### Configuration Schema
See [CONFIG_REFERENCE.md](../../../docs/CONFIG_REFERENCE.md) for complete schema documentation.

---
*Pipeline Module | Central orchestration | Builder pattern | Configuration-driven processing*