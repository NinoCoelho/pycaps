# pycaps v0.3.0 Release Notes

## 🚀 Faster-Whisper Integration for 4x Speed Improvement

We're excited to announce pycaps v0.3.0, featuring integration with faster-whisper for dramatically improved transcription performance and reduced hallucinations!

### ⚡ Performance Highlights

- **4x faster transcription** compared to OpenAI Whisper
- **65-second total processing** for a 4.5-minute video (vs >5 minutes previously)
- **40% lower memory usage** through CTranslate2 optimization
- **Built-in anti-hallucination** measures that actually work

### 🎯 Key Features

#### New FasterWhisperTranscriber
A drop-in replacement for WhisperAudioTranscriber with superior performance:

```python
from pycaps.transcriber import FasterWhisperTranscriber

transcriber = FasterWhisperTranscriber(
    model_size="base",
    language="pt",
    use_vad=True,  # Built-in Voice Activity Detection
    hallucination_silence_threshold=2.0
)
```

#### CLI Integration
Use faster-whisper directly from the command line:

```bash
# Simple usage
pycaps render video.mp4 output.mp4 --faster-whisper

# With options
pycaps render video.mp4 output.mp4 \
  --faster-whisper \
  --template redpill \
  --lang pt \
  --whisper-model base
```

#### Pipeline Builder Support
```python
from pycaps.pipeline import CapsPipelineBuilder

pipeline = (CapsPipelineBuilder()
    .with_input_video("input.mp4")
    .with_faster_whisper(
        model_size="base",
        language="pt"
    )
    .with_template("hype")
    .build())
```

### 🛡️ Anti-Hallucination Improvements

FasterWhisperTranscriber includes several measures to prevent hallucinations:

1. **`condition_on_previous_text=False`** - Prevents context-based loops
2. **Hallucination silence threshold** - Better handling of silence
3. **Repetition penalty** - Reduces duplicate outputs
4. **Common phrase detection** - Filters YouTube-style artifacts

### 📊 Real-World Performance

Testing with a 4.5-minute Portuguese video:

| Method | Transcription Time | Total Time | Issues |
|--------|-------------------|------------|--------|
| Whisper + Anti-hallucination (v0.2.0) | >60s | >5 min | Often hangs |
| **Faster-Whisper (v0.3.0)** | **11s** | **65s** | **None** |

### 🔧 Technical Details

- **New dependency**: `faster-whisper>=1.2.0`
- **Backend**: CTranslate2 for optimized inference
- **Compatibility**: Works with existing pycaps configurations
- **Models**: Supports all Whisper model sizes (tiny to large-v3)

### 💻 Installation

```bash
# Upgrade existing installation
pip install --upgrade pycaps

# Fresh installation
pip install pycaps>=0.3.0
```

### 🔄 Migration Guide

#### For Standard Use Cases
No changes needed! Your existing code continues to work.

#### To Use Faster-Whisper
Simply add the `--faster-whisper` flag to CLI commands or use `with_faster_whisper()` in Python:

```python
# Old way (still works)
pipeline.with_whisper_config(model_size="base")

# New way (4x faster)
pipeline.with_faster_whisper(model_size="base")
```

### 🐛 Bug Fixes

- Fixed punctuation handling syntax errors
- Improved Word and Segment model compatibility
- Better ElementContainer handling in document structure
- Fixed device/compute_type parameter initialization

### 📝 Documentation Updates

- Updated CHANGELOG.md with v0.3.0 changes
- New examples in README.md
- Updated transcriber module documentation
- Enhanced CLI reference documentation

### 🙏 Acknowledgments

Thanks to the SYSTRAN team for creating faster-whisper and to our community for reporting the hallucination issues that led to this improvement!

### 📚 Links

- [GitHub Repository](https://github.com/francozanardi/pycaps)
- [Documentation](https://github.com/francozanardi/pycaps/tree/main/docs)
- [Issue Tracker](https://github.com/francozanardi/pycaps/issues)

---

**Note**: This release maintains full backward compatibility. All existing features from v0.2.0 (anti-hallucination system) and earlier versions continue to work as expected.