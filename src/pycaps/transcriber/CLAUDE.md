# Transcriber Module - Claude Context

**Module Type:** Audio Transcription & Subtitle Import Processing
**Primary Technologies:** OpenAI Whisper, Google Speech API, Audio Processing
**Dependencies:** torch, librosa, pydub, google-cloud-speech, webvtt
**Last Updated:** 2025-08-21

## Module Overview

The Transcriber module handles speech-to-text conversion and subtitle file import with word-level timestamps, providing the foundation for all subtitle generation in pycaps. It supports multiple transcription backends, SRT file import with intelligent timing estimation, intelligent audio preprocessing, and sophisticated text segmentation strategies. The module is designed for high accuracy and performance with extensive customization options.

### Core Capabilities
- Multi-provider transcription (Whisper, Google Speech, custom providers)
- **SRT file import with intelligent word-level timing estimation**
- Word-level timestamp extraction with high precision
- Intelligent audio preprocessing and enhancement
- Multiple segmentation strategies for natural text grouping
- Interactive transcription editing interface
- Batch processing for multiple audio sources
- Language detection and multilingual support

## Architecture & Design

### Transcription Pipeline
```
Audio Input → Preprocessing → Speech Recognition → Timestamp Alignment → 
Segmentation → Validation → Transcription Output
```

### Provider Architecture
```
BaseTranscriber
├── WhisperTranscriber (primary)
├── GoogleSpeechTranscriber
├── AzureSpeechTranscriber
├── SRTTranscriber (subtitle import)
└── CustomTranscriber (extensible)
```

## Key Components

### 1. Base Transcriber (`base_transcriber.py`)

**Purpose**: Abstract interface for all transcription providers
**Key Features**:
- Standardized transcription interface
- Provider-agnostic result format
- Configuration validation
- Error handling framework

```python
class BaseTranscriber(ABC):
    @abstractmethod
    async def transcribe(self, audio_file: str) -> TranscriptionResult
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]
    
    @abstractmethod
    def validate_config(self, config: dict) -> bool
```

### 2. Whisper Audio Transcriber (`whisper_audio_transcriber.py`)

**Purpose**: OpenAI Whisper integration for high-quality transcription with Portuguese language optimizations
**Model Options**:
- **tiny** - Fastest, least accurate (~32x realtime)
- **base** - Balanced speed/accuracy (~16x realtime)
- **small** - Good accuracy (~6x realtime)
- **medium** - High accuracy (~2x realtime)
- **large** - Highest accuracy (~1x realtime)
- **large-v2** - Latest improvements
- **large-v3** - Current best model

**Key Features**:
- **Portuguese Language Optimizations**: Specialized compound word processing and religious vocabulary recognition
- **Repetition Filtering**: Intelligent removal of repetitive segments that Whisper sometimes generates
- **Custom Vocabulary Support**: User-provided Portuguese terms for better recognition
- **Enhanced Prompt Engineering**: Optimized initial prompts for Portuguese transcription

```python
class WhisperAudioTranscriber(AudioTranscriber):
    def __init__(self, model_size: str = "medium", language: Optional[str] = None, 
                 model: Optional[Any] = None, initial_prompt: Optional[str] = None, 
                 portuguese_vocabulary: Optional[List[str]] = None):
        """
        Transcribes audio using OpenAI's Whisper model with Portuguese optimizations.
        
        Args:
            model_size: Size of the Whisper model to use (e.g., "tiny", "base", "medium").
            language: Language of the audio (e.g., "en", "pt").
            model: (Optional) A pre-loaded Whisper model instance.
            initial_prompt: Custom prompt to guide transcription (max 244 tokens).
            portuguese_vocabulary: List of Portuguese compound/religious terms to recognize.
        """
    
    def transcribe(self, audio_path: str) -> Document:
        # Enhanced Whisper parameters for better accuracy
        result = self._get_model().transcribe(
            audio_path,
            word_timestamps=True,
            language=self._language,
            initial_prompt=prompt,
            temperature=0.0,  # More deterministic output
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            condition_on_previous_text=False,  # Prevent repetition loops
            suppress_tokens=[-1]
        )
        
        # Apply Portuguese post-processing and repetition removal
        if self._language == "pt" or not self._language:
            document = self._post_process_portuguese_compounds(document)
        document = self._remove_repetitive_segments(document)
        
        return document
```

**Portuguese Optimizations**:
- **Compound Word Processing**: Fixes split reflexive verbs (e.g., "ajoelhou se" → "ajoelhou-se")
- **Religious Vocabulary**: Specialized recognition for biblical terms like "Getsêmani"
- **Prefix Handling**: Proper handling of Portuguese prefixes (bem-, mal-, auto-, anti-, etc.)
- **Repetition Detection**: Removes excessive repetitive segments from transcription output

**Configuration Options**:
```json
{
  "provider": "whisper",
  "model": "base",
  "language": "auto",
  "options": {
    "temperature": 0.0,
    "compression_ratio_threshold": 2.4,
    "logprob_threshold": -1.0,
    "no_speech_threshold": 0.6,
    "condition_on_previous_text": true,
    "initial_prompt": ""
  }
}
```

### 3. Google Speech Transcriber (`google_speech_transcriber.py`)

**Purpose**: Google Cloud Speech-to-Text integration
**Key Features**:
- Real-time and batch transcription
- Enhanced model support
- Speaker diarization
- Automatic punctuation
- Profanity filtering

```python
class GoogleSpeechTranscriber(BaseTranscriber):
    def __init__(self, credentials_path: str = None):
        self.client = speech.SpeechClient.from_service_account_file(
            credentials_path
        ) if credentials_path else speech.SpeechClient()
    
    async def transcribe(self, audio_file: str) -> TranscriptionResult:
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_word_time_offsets=True,
            enable_automatic_punctuation=True,
            model="latest_long"
        )
        
        response = self.client.recognize(config=config, audio=audio)
        return self._process_google_result(response)
```

### 4. SRT Transcriber (`srt_transcriber.py`)

**Purpose**: SRT subtitle file import with intelligent word-level timing estimation
**Key Features**:
- Parse standard SRT format files
- Convert segment-level timing to word-level estimates
- Handle HTML tag cleaning and text normalization
- Support multiple encodings (UTF-8, Latin-1)
- Intelligent word timing distribution based on text characteristics

```python
class SRTTranscriber(AudioTranscriber):
    def __init__(self, srt_path: str):
        self.srt_path = srt_path
    
    def transcribe(self, audio_path: str) -> Document:
        # Load SRT entries
        srt_entries = SRTLoader.load_srt(self.srt_path)
        
        # Convert to Document structure with word-level timing
        document = Document()
        for srt_entry in srt_entries:
            segment = self._create_segment_from_srt_entry(srt_entry)
            document.segments.add(segment)
        
        return document
```

**Word Timing Algorithm**:
The SRT transcriber estimates individual word timings using:
- Word length and syllable count estimation
- Text complexity analysis (numbers, punctuation)
- Proportional time distribution within segment duration
- Natural speech pattern considerations

### 5. SRT Loader (`srt_loader.py`)

**Purpose**: Robust SRT file parsing and validation utility
**Key Features**:
- Parse standard SRT timestamp format
- Clean HTML-like formatting tags
- Handle encoding variations
- Validate SRT structure and timing

```python
class SRTLoader:
    @classmethod
    def load_srt(cls, srt_path: str) -> List[SRTEntry]:
        # Handles file reading, parsing, and validation
        return parsed_entries
```

### 6. Audio Preprocessing (`audio_processor.py`)

**Purpose**: Enhance audio quality for better transcription accuracy
**Processing Steps**:

1. **Format Normalization**
   ```python
   def normalize_audio(audio_file: str) -> str:
       audio = AudioSegment.from_file(audio_file)
       
       # Convert to mono 16kHz WAV
       normalized = audio.set_channels(1).set_frame_rate(16000)
       
       # Normalize volume
       normalized = normalized.normalize()
       
       output_path = tempfile.mktemp(suffix=".wav")
       normalized.export(output_path, format="wav")
       return output_path
   ```

2. **Noise Reduction**
   ```python
   def reduce_noise(audio_file: str) -> str:
       # Load audio with librosa
       y, sr = librosa.load(audio_file, sr=16000)
       
       # Apply spectral subtraction
       cleaned = noisereduce.reduce_noise(y=y, sr=sr)
       
       # Save processed audio
       output_path = tempfile.mktemp(suffix=".wav")
       sf.write(output_path, cleaned, sr)
       return output_path
   ```

3. **Voice Activity Detection**
   ```python
   def detect_speech_segments(audio_file: str) -> List[Tuple[float, float]]:
       # Use VAD to identify speech segments
       vad = webrtcvad.Vad(3)  # Aggressiveness level 3
       
       segments = []
       # Process audio in chunks
       for start, end, is_speech in process_audio_chunks(audio_file):
           if is_speech:
               segments.append((start, end))
       
       return merge_close_segments(segments)
   ```

### 7. Segmentation Strategies (`splitter/`)

**Purpose**: Intelligent text segmentation for natural subtitle grouping

#### Sentence Splitter (`sentence_splitter.py`)
```python
class SentenceSplitter(BaseSegmentSplitter):
    def split(self, transcription: TranscriptionResult) -> List[Segment]:
        sentences = self._detect_sentences(transcription.text)
        segments = []
        
        for sentence in sentences:
            words = self._extract_words_for_sentence(sentence, transcription)
            segment = Segment(
                text=sentence,
                words=words,
                start_time=words[0].start_time,
                end_time=words[-1].end_time
            )
            segments.append(segment)
        
        return segments
```

#### Time-Based Splitter (`time_splitter.py`)
```python
class TimeSplitter(BaseSegmentSplitter):
    def __init__(self, max_duration: float = 3.0):
        self.max_duration = max_duration
    
    def split(self, transcription: TranscriptionResult) -> List[Segment]:
        segments = []
        current_words = []
        segment_start = 0
        
        for word in transcription.words:
            current_words.append(word)
            
            if (word.end_time - segment_start) >= self.max_duration:
                segments.append(self._create_segment(current_words))
                current_words = []
                segment_start = word.end_time
        
        if current_words:
            segments.append(self._create_segment(current_words))
        
        return segments
```

#### Smart Splitter (`smart_splitter.py`)
```python
class SmartSplitter(BaseSegmentSplitter):
    def __init__(self, max_words: int = 8, max_duration: float = 4.0):
        self.max_words = max_words
        self.max_duration = max_duration
    
    def split(self, transcription: TranscriptionResult) -> List[Segment]:
        # Combine multiple strategies
        candidates = []
        
        # Try sentence boundaries
        sentence_splits = self._split_by_sentences(transcription)
        candidates.extend(sentence_splits)
        
        # Try natural pauses
        pause_splits = self._split_by_pauses(transcription)
        candidates.extend(pause_splits)
        
        # Try semantic boundaries
        semantic_splits = self._split_by_semantics(transcription)
        candidates.extend(semantic_splits)
        
        # Score and select best segmentation
        return self._select_best_segmentation(candidates)
```

### 8. Interactive Editor (`editor/`)

**Purpose**: GUI for manual transcription correction and timing adjustment

#### Editor Interface (`transcription_editor.py`)
```python
class TranscriptionEditor:
    def __init__(self, transcription: TranscriptionResult):
        self.transcription = transcription
        self.ui = self._create_ui()
        self.audio_player = AudioPlayer()
    
    def show_editor(self) -> TranscriptionResult:
        # Launch GUI with waveform display
        waveform = self._generate_waveform()
        word_timeline = self._create_word_timeline()
        
        self.ui.display_waveform(waveform)
        self.ui.display_timeline(word_timeline)
        self.ui.show()
        
        return self.get_edited_result()
    
    def _create_ui(self):
        # Create PyQt/Tkinter interface
        # - Audio waveform display
        # - Word-level editing
        # - Timing adjustment
        # - Playback controls
        pass
```

### 9. Transcription Result (`transcription_result.py`)

**Purpose**: Standardized output format for all transcription providers

```python
@dataclass
class Word:
    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    speaker_id: Optional[str] = None

@dataclass
class Segment:
    text: str
    words: List[Word]
    start_time: float
    end_time: float
    speaker_id: Optional[str] = None
    confidence: float = 1.0

@dataclass
class TranscriptionResult:
    text: str
    words: List[Word]
    segments: List[Segment]
    language: str
    confidence: float
    processing_time: float
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Language Support

### Supported Languages
```python
SUPPORTED_LANGUAGES = {
    "auto": "Auto-detect",
    "en": "English",
    "es": "Spanish", 
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    # ... 50+ more languages
}
```

### Language Detection
```python
def detect_language(audio_file: str) -> str:
    # Use Whisper's built-in language detection
    model = whisper.load_model("base")
    audio = whisper.load_audio(audio_file)
    audio_trimmed = audio[:30 * 16000]  # First 30 seconds
    
    _, probs = model.detect_language(audio_trimmed)
    detected_lang = max(probs, key=probs.get)
    
    return detected_lang if probs[detected_lang] > 0.5 else "en"
```

## Performance Optimization

### Model Caching
```python
class ModelCache:
    _instances = {}
    
    @classmethod
    def get_whisper_model(cls, model_name: str):
        if model_name not in cls._instances:
            cls._instances[model_name] = whisper.load_model(model_name)
        return cls._instances[model_name]
```

### Batch Processing
```python
async def transcribe_batch(
    audio_files: List[str], 
    config: TranscriberConfig
) -> List[TranscriptionResult]:
    
    # Process in parallel with concurrency limit
    semaphore = asyncio.Semaphore(config.max_concurrent)
    
    async def transcribe_single(audio_file: str):
        async with semaphore:
            return await transcriber.transcribe(audio_file)
    
    tasks = [transcribe_single(f) for f in audio_files]
    results = await asyncio.gather(*tasks)
    
    return results
```

### GPU Acceleration
```python
def setup_gpu_transcription():
    if torch.cuda.is_available():
        device = "cuda"
        torch.cuda.empty_cache()
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = "mps"  # Apple Silicon
    else:
        device = "cpu"
    
    return device
```

## Error Handling & Recovery

### Common Error Scenarios
1. **Audio Format Issues** - Unsupported or corrupted audio
2. **Network Errors** - API service unavailable
3. **Memory Issues** - Large audio files causing OOM
4. **Model Loading Failures** - Missing or corrupted models
5. **Language Detection Errors** - Unclear or mixed languages

### Recovery Strategies
```python
async def transcribe_with_fallback(
    audio_file: str, 
    primary_config: dict,
    fallback_configs: List[dict]
) -> TranscriptionResult:
    
    configs = [primary_config] + fallback_configs
    
    for i, config in enumerate(configs):
        try:
            transcriber = create_transcriber(config)
            return await transcriber.transcribe(audio_file)
        except Exception as e:
            if i == len(configs) - 1:  # Last attempt
                raise TranscriptionError(f"All transcription attempts failed: {e}")
            else:
                logger.warning(f"Transcription attempt {i+1} failed: {e}")
                continue
```

## Configuration Examples

### High-Quality Configuration
```json
{
  "provider": "whisper",
  "model": "large-v3",
  "language": "auto",
  "preprocessing": {
    "normalize_audio": true,
    "reduce_noise": true,
    "voice_activity_detection": true
  },
  "segmentation": {
    "strategy": "smart",
    "max_words_per_segment": 6,
    "max_duration_per_segment": 3.5
  },
  "postprocessing": {
    "fix_capitalization": true,
    "add_punctuation": true,
    "filter_filler_words": false
  }
}
```

### Fast Processing Configuration
```json
{
  "provider": "whisper",
  "model": "tiny",
  "language": "en",
  "preprocessing": {
    "normalize_audio": true,
    "reduce_noise": false,
    "voice_activity_detection": false
  },
  "segmentation": {
    "strategy": "time",
    "max_duration_per_segment": 4.0
  }
}
```

## Integration Points

### Pipeline Integration
```python
from ..pipeline import CapsPipeline

# Transcriber is called early in pipeline
transcription = await transcriber.transcribe(audio_file)
document = DocumentBuilder.from_transcription(transcription)
```

### Template Integration
```python
from ..template import TemplateLoader

# Templates can specify transcription preferences
template = TemplateLoader.load("hype")
transcriber_config = template.get_transcriber_config()
```

## Development Workflows

### Testing Transcription
```python
import pytest
from pycaps.transcriber import WhisperTranscriber

@pytest.mark.asyncio
async def test_whisper_transcription():
    transcriber = WhisperTranscriber(model="tiny")
    result = await transcriber.transcribe("test_audio.wav")
    
    assert result.text is not None
    assert len(result.words) > 0
    assert all(w.start_time <= w.end_time for w in result.words)
```

### Custom Provider Development
```python
class CustomTranscriber(BaseTranscriber):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def transcribe(self, audio_file: str) -> TranscriptionResult:
        # Implement custom transcription logic
        pass
    
    def get_supported_formats(self) -> List[str]:
        return ["wav", "mp3", "m4a"]
    
    def validate_config(self, config: dict) -> bool:
        return "api_key" in config
```

## Troubleshooting Guide

### Common Issues

1. **Whisper Model Download Issues**
   ```bash
   # Pre-download models
   python -c "import whisper; whisper.load_model('base')"
   ```

2. **Audio Format Problems**
   ```python
   # Convert audio format
   from pydub import AudioSegment
   audio = AudioSegment.from_file("input.mp4")
   audio.export("output.wav", format="wav")
   ```

3. **Memory Issues with Large Files**
   ```python
   # Process in chunks
   def transcribe_large_file(audio_file: str, chunk_duration: int = 300):
       chunks = split_audio_into_chunks(audio_file, chunk_duration)
       results = []
       for chunk in chunks:
           result = transcriber.transcribe(chunk)
           results.append(result)
       return merge_transcription_results(results)
   ```

4. **Poor Transcription Quality**
   - Use larger Whisper model
   - Enable audio preprocessing
   - Check audio quality and format
   - Ensure proper language setting

## API Reference

### Core Classes
- **`BaseTranscriber`** - Abstract transcription interface
- **`WhisperTranscriber`** - Whisper implementation
- **`GoogleSpeechTranscriber`** - Google Speech implementation
- **`SRTTranscriber`** - SRT file import with intelligent timing
- **`SRTLoader`** - SRT file parsing and validation utility
- **`TranscriptionResult`** - Standardized output format
- **`AudioProcessor`** - Audio preprocessing utilities

### Key Methods
- **`transcribe(audio_file)`** - Main transcription method
- **`get_supported_formats()`** - List supported audio formats
- **`validate_config(config)`** - Validate configuration
- **`detect_language(audio)`** - Automatic language detection

---
*Transcriber Module | Speech-to-text | Word-level timestamps | Multi-provider support*