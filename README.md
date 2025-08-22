# pycaps

[![Version](https://img.shields.io/badge/version-0.3.0-green.svg)](https://github.com/francozanardi/pycaps)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/francozanardi/pycaps)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Try%20it%20online-Hugging%20Face-blue?logo=huggingface)](https://huggingface.co/spaces/francozanardi/pycaps)


**pycaps** is a Python tool for adding CSS styled subtitles to videos. It's designed as both a programmable library and a command-line interface (CLI), making it perfect for automating the creation of dynamic content for platforms like TikTok, YouTube Shorts, and Instagram Reels.

![demo-1](https://github.com/user-attachments/assets/fd2d3325-c986-4b6a-81ba-09c428577e61)
![demo-2](https://github.com/user-attachments/assets/9a789244-0387-4ac8-ab51-b3601447953e)

<sub>See more examples on <a href="https://www.pycaps.com/">pycaps.com</a></sub>

## Try It Online (no installation needed!)

You have two options to test `pycaps` directly in your browser. Choose the one that best fits your needs.

### 1. Interactive Web Demo (on Hugging Face)

Ideal for a **quick preview**, testing built-in templates, and **editing captions** with a user-friendly interface.

[![Hugging Face Spaces](https://img.shields.io/badge/Launch%20Web%20Demo-Hugging%20Face-blue?logo=huggingface)](https://huggingface.co/spaces/francozanardi/pycaps)

> **Keep in mind:**
> *   This demo runs on a shared, CPU-only environment, so it's best for **short videos (< 60 seconds)**.
> *   For a private, faster experience, you can **[duplicate the Space](https://huggingface.co/spaces/francozanardi/pycaps?duplicate=true)** for free.

### 2. Full-Power Notebook (on Google Colab)

The best choice for **processing longer videos** with **maximum transcription quality**, using a free GPU provided by Google.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/117g6xujecjLyXHBwhwyzx0innCMLh_nj?usp=sharing)

> **Keep in mind:**
> *   The interface is a step-by-step code notebook, not a graphical UI.
> *   You will be guided to enable the GPU for the best performance.

## Key Features

*   **🚀 Faster-Whisper Support** (v0.3.0): 4x faster transcription with 40% less memory usage and built-in anti-hallucination measures.
*   **Template System**: Get started quickly with 14+ predefined templates. Create and share your own templates, packaging styles, animations, and configurations.
*   **CSS Styling**: Style subtitles using standard CSS. Target specific states like `.word-being-narrated` for dynamic effects, cleanly separating style from logic.
*   **Word Tagging**: Tag words or phrases using regular expressions, word lists, or AI. These tags act as powerful selectors for applying custom CSS, effects, or animations.
*   **Advanced Animations & Effects**: Bring words to life with a library of built-in animations (fades, pops, slides) and effects (typewriting, emoji insertion, sound effects).
*   **Anti-Hallucination System** (v0.2.0+): Advanced transcription with VAD preprocessing and smart chunking for long videos.
*   **SRT Import**: Skip transcription entirely by importing existing SRT subtitle files with intelligent word-level timing estimation.
*   **Dual Interface**: Use it as a simple CLI for quick renders or as a comprehensive Python library for programmatic video creation.
*   **Offline-First**: The core transcription, styling, and rendering engine runs entirely on your local machine. An internet connection is only needed for optional AI-powered features.

## Prerequisites

Before installing, please ensure your environment meets the following requirements:

*   **Python Version**: `pycaps` was tested on **Python 3.10, 3.11, and 3.12**. Other versions may present issues.

*   **FFmpeg**: You need to have FFmpeg installed on your system and accessible from your command line's `PATH`. This is essential for all audio and video processing tasks.
    *   You can download it from [ffmpeg.org](https://ffmpeg.org/download.html) and follow a guide to add it to your system's `PATH`.

## Installation

pycaps is currently in a very alpha stage and is not yet available on PyPI. You can install it directly from the GitHub repository.

1.  **Install FFmpeg**: Ensure you have completed the prerequisite step above.

2.  **Install pycaps from GitHub:**
    ```bash
    pip install git+https://github.com/francozanardi/pycaps.git
    ```

3.  **Install Browser Dependencies for Rendering:**
    `pycaps` uses Playwright to render CSS styles. You need to install its browser dependency (this is a one-time setup):
    ```bash
    playwright install chromium
    ```

> ⚠️ **Note**: The first time you use `pycaps`, it will download the transcription model (Whisper or Faster-Whisper). This may take a few minutes and only happens once.

## Quick Start

There are two primary ways to use pycaps: via the command line with a template or programmatically in a Python script.

### 1. Using the Command-Line (CLI)

The fastest way to get started is to use a built-in template.

```bash
# Standard transcription
pycaps render --input my_video.mp4 --template minimalist

# 4x faster transcription (v0.3.0+)
pycaps render --input my_video.mp4 --template minimalist --faster-whisper

# Use existing subtitles (skip transcription)
pycaps render --input my_video.mp4 --template hype --srt-file subtitles.srt
```

This command will:
1.  Load the chosen template (14+ available: minimalist, hype, redpill, fast, etc.).
2.  Transcribe the audio or import SRT subtitles.
3.  Apply the template's styles and animations.
4.  Save the result in a new file.

### 2. Using the Python Library

For full control, use the `CapsPipelineBuilder` in your Python code.

```python
from pycaps import CapsPipelineBuilder

# Standard pipeline
pipeline = (
    CapsPipelineBuilder()
    .with_input_video("input.mp4")
    .add_css("css_file.css")
    .build()
)
pipeline.run()

# Using Faster-Whisper for 4x speed (v0.3.0+)
pipeline = (
    CapsPipelineBuilder()
    .with_input_video("input.mp4")
    .with_faster_whisper(model_size="base", language="auto")
    .with_template("hype")
    .build()
)
pipeline.run()
```

You can also preload the builder using a Template.
```python
from pycaps import *

# Load a template and configure it
builder = TemplateLoader("default").with_input_video("my_video.mp4").load(False)

# Programmatically add an animation
builder.add_animation(
    animation=FadeIn(),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.SEGMENT
)

# Build and run the pipeline
pipeline = builder.build()
pipeline.run()
```

## Performance & Transcription Options

### 🚀 Faster-Whisper (v0.3.0+)
For production use, we recommend using Faster-Whisper for significantly improved performance:

| Model | Standard Whisper | Faster-Whisper | Speed Improvement |
|-------|-----------------|----------------|-------------------|
| tiny  | ~32x realtime   | ~128x realtime | **4x faster**     |
| base  | ~16x realtime   | ~64x realtime  | **4x faster**     |
| small | ~6x realtime    | ~24x realtime  | **4x faster**     |
| medium| ~2x realtime    | ~8x realtime   | **4x faster**     |

**Additional benefits:**
- 40% less memory usage
- Built-in VAD (Voice Activity Detection)
- Better handling of silence and non-speech
- Reduced hallucinations on long videos

### Anti-Hallucination System (v0.2.0+)
For videos longer than 90 seconds, pycaps includes advanced anti-hallucination features:
- VAD preprocessing to detect speech segments
- Smart chunking with overlapping segments
- Compression ratio and semantic similarity filtering
- Preset configurations: `maximum_quality`, `balanced`, `podcasts`, `short_videos`

## Available Templates

pycaps includes 14+ built-in templates to get you started quickly:

- **minimalist** - Clean, simple subtitles
- **hype** - High-energy animated subtitles
- **redpill** - Red pill-shaped styling with drop shadows
- **fast** - Quick rendering with minimal effects
- **bold** - Strong, impactful text
- **neon** - Glowing neon effect
- **retro** - Vintage aesthetic
- **modern** - Contemporary design
- **comic** - Comic book style
- **gradient** - Color gradient effects
- **shadow** - Drop shadow emphasis
- **outline** - Text with outlines
- **glow** - Soft glowing text
- **wave** - Animated wave effects

## What's Next?

*   🚀 **For Command-Line Users**: Check the **[CLI Usage Guide](./docs/CLI.md)** for a quick and easy start.
*   🧠 **For Developers**: Understand the core concepts in the **[Structure Guide](./docs/CORE_STRUCTURE.md)**.
*   🏷️ **Styling & Logic**: Learn about the powerful **[Tagging System](./docs/TAGS.md)**.
*   🎨 **Reusable Styles**: See how **[Templates](./docs/TEMPLATES.md)** work and how to create your own.
*   💡 **Inspiration**: Dive into **[Code & JSON Examples](./docs/EXAMPLES.md)**.
*   🔧 **Advanced Config**: See all options in the **[JSON Configuration Reference](./docs/CONFIG_REFERENCE.md)**.
*   🤖 **AI Features**: Learn about AI-powered features in the **[API Usage Guide](./docs/API_USAGE.md)**.

## Contributing

This project is in active development. Contributions, bug reports, and feature requests are welcome! Please open an issue or pull request on our [GitHub repository](https://github.com/francozanardi/pycaps).

## License

pycaps is licensed under the [MIT License](https://opensource.org/licenses/MIT).
