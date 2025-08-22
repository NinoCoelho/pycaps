# Code & JSON Examples

This page contains practical examples of using `pycaps`, ranging from simple configurations to advanced programmatic pipelines.

---
## Example 1: Minimal JSON Configuration

This is a bare-bones `config.json` for a quick render. It defines the input/output, styles, and a simple animation.

**`config.json`**
```json
{
  "input": "video.mp4",
  "output": "video_with_subs.mp4",
  "css": "styles.css",
  "layout": {
    "max_number_of_lines": 2
  },
  "animations": [
    {
      "type": "fade_in",
      "when": "narration-starts",
      "what": "segment",
      "duration": 0.3
    }
  ]
}
```

**`styles.css`**
```css
.word {
  font-size: 30px;
  color: white;
  text-shadow: 2px 2px 5px black;
}
.word-being-narrated {
  color: yellow;
}
```

**To run this, you can use the CLI:**
```bash
pycaps render --config config.json
```

Or, you can also do it from Python:
```python
from pycaps import JsonConfigLoader

loader = JsonConfigLoader("config.json")
pipeline = loader.load() # you can use loader.load(False) if you can receive the builder 
pipeline.run()
```

---
## Example 2: Basic Python Script

This example shows how to build a pipeline programmatically in Python, adding a simple pop-in animation to each word.

```python
from pycaps import CapsPipelineBuilder
from pycaps.animation import PopIn
from pycaps.common import EventType, ElementType

# 1. Initialize the builder
builder = CapsPipelineBuilder()

# 2. Configure the pipeline
builder.with_input_video("my_video.mp4")
builder.add_css("path/to/my_styles.css")
builder.add_animation(
    animation=PopIn(duration=0.3),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.WORD
)

# 3. Build and run
pipeline = builder.build()
pipeline.run()

print("Video has been rendered!")
```

---
## Example 3: SRT File Import with Python

This example shows how to use an existing SRT subtitle file instead of transcribing audio, which significantly speeds up processing.

**`process_with_srt.py`**
```python
from pycaps.pipeline import CapsPipelineBuilder

# Create pipeline with SRT file input
builder = CapsPipelineBuilder()
pipeline = (builder
    .with_input_video("my_video.mp4")
    .with_output_video("styled_subtitles.mp4")
    .with_srt_file("subtitles.srt")  # Use existing SRT file
    .with_template("hype")           # Apply styling template
    .build())

# Run the pipeline
pipeline.run()

print("SRT-based video has been rendered!")
```

**`subtitles.srt`** (example SRT file)
```srt
1
00:00:00,000 --> 00:00:02,500
Welcome to our presentation today.

2
00:00:02,500 --> 00:00:05,000
We'll be discussing the latest innovations.

3
00:00:05,000 --> 00:00:08,000
These technologies will change everything.
```

**Benefits of SRT Import:**
- **Faster Processing**: Skips audio transcription entirely
- **Precise Control**: Use professionally created subtitles
- **Multiple Languages**: Works with any language SRT file
- **Full Styling**: All pycaps templates and effects still apply

---
## Example 4: Faster-Whisper Transcription (v0.3.0)

This example shows how to use the new Faster-Whisper integration for 4x faster transcription with better anti-hallucination capabilities.

**`faster_transcription.py`**
```python
from pycaps.pipeline import CapsPipelineBuilder

# Method 1: Using pipeline builder with faster-whisper
builder = CapsPipelineBuilder()
pipeline = (builder
    .with_input_video("my_video.mp4")
    .with_output_video("output.mp4")
    .with_faster_whisper(
        model_size="base",         # Options: tiny, base, small, medium, large, large-v2
        device="cpu",              # Use "cuda" for GPU acceleration
        language="auto",           # Auto-detect or specify: en, pt, es, etc.
        use_vad=True              # Enable Voice Activity Detection
    )
    .with_template("hype")
    .build())

pipeline.run()
print("Video rendered with Faster-Whisper!")

# Method 2: Direct instantiation
from pycaps import CapsPipeline
from pycaps.transcriber import FasterWhisperTranscriber

transcriber = FasterWhisperTranscriber(
    model_size="medium",
    device="cuda" if torch.cuda.is_available() else "cpu",
    language="pt",  # Portuguese
    use_vad=True,
    vad_threshold=0.5,
    condition_on_previous_text=False,  # Prevent hallucinations
    repetition_penalty=1.1
)

pipeline = CapsPipeline(transcriber=transcriber)
pipeline.process("input.mp4", "output.mp4")
```

**Benefits of Faster-Whisper:**
- **4x Speed Improvement**: Base model runs at ~64x realtime vs Whisper's ~16x
- **40% Less Memory**: More efficient memory usage
- **Built-in VAD**: Better silence handling
- **Reduced Hallucinations**: Built-in anti-hallucination measures
- **GPU Support**: CUDA acceleration available

**CLI Usage:**
```bash
# Use faster-whisper with CLI
pycaps render --input video.mp4 --output result.mp4 --faster-whisper --template hype

# With custom model size
pycaps render --input video.mp4 --faster-whisper --whisper-model medium --template modern
```

---
## Example 5: Advanced JSON with Tagger and Effects

This example demonstrates a more complex setup using a JSON file. It uses a wordlist to tag specific words and applies a sound effect to them.

**`my_template/pycaps.template.json`**
```json
{
  "css": "style.css",
  "layout": {
    "max_width_ratio": 0.85,
    "vertical_align": { "align": "bottom", "offset": -0.05 }
  },
  "tagger_rules": [
    {
      "type": "wordlist",
      "tag": "special-word",
      "filename": "special_words.txt"
    }
  ],
  "sound_effects": [
    {
      "type": "preset",
      "name": "ding-short",
      "when": "narration-starts",
      "what": "word",
      "tag_condition": "special-word"
    }
  ]
}
```

**`my_template/special_words.txt`**
```
pycaps
amazing
wow
```

**`my_template/style.css`**
```css
.word {
  color: white;
  font-size: 25px;
}

.word.special-word {
  color: #34d399; /* A nice green color */
  font-weight: bold;
}
```

**To run this, use the template:**
```bash
pycaps render --input video.mp4 --template my_template
```

---
## Example 6: Advanced Python Script with Custom Logic

This script showcases the full power of the Python library. It defines a complex pipeline with multiple animations, conditional effects, and custom taggers.

```python
from pycaps import *

# --- 1. Create a custom tagger ---
tagger = SemanticTagger()
tagger.add_regex_rule(Tag("shoutout"), r"(?i)shoutout to \w+")
tagger.add_wordlist_rule(Tag("important"), ["key", "critical", "important"])
# or you can use ai here: tagger.add_ai_rule(Tag("important"), "most important phrases or words")

# --- 2. Build the pipeline ---
builder = CapsPipelineBuilder()
builder.with_input_video("podcast_clip.mp4")
builder.with_output_video("podcast_clip_final.mp4")
builder.with_video_quality(VideoQuality.HIGH)
builder.with_semantic_tagger(tagger) # Use our custom tagger
builder.add_css("styles.css")

# --- 3. Add Effects ---
# Remove trailing commas and periods
builder.add_effect(RemovePunctuationMarksEffect(
    punctuation_marks=[".", ","],
    exception_marks=["..."]
))
# Add a whoosh sound only on the first line of a segment
builder.add_effect(SoundEffect(
    sound=BuiltinSound.WHOOSH,
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.LINE,
    tag_condition=TagConditionFactory.HAS(BuiltinTag.FIRST_LINE_IN_SEGMENT)
))

# --- 4. Add Animations ---
builder.add_animation(
    animation=SlideIn(direction="left"),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.SEGMENT,
    tag_condition=TagConditionFactory.HAS(BuiltinTag.FIRST_LINE_IN_SEGMENT
)
builder.add_animation(
    animation=SlideIn(direction="right"),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.SEGMENT,
    tag_condition=TagConditionFactory.HAS(BuiltinTag.LAST_LINE_IN_SEGMENT
)
# "Important" words zoom out when spoken
builder.add_animation(
    animation=ZoomOut(duration=0.2),
    when=EventType.ON_NARRATION_STARTS,
    what=ElementType.WORD,
    tag_condition=TagConditionFactory.parse("important")
)

# --- 5. Build and Run ---
pipeline = builder.build()
pipeline.run()

print("Advanced pipeline finished successfully!")