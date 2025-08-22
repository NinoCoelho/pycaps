# Meta Prompt: English to Portuguese Video Subtitle Generation System

## System Overview
You are implementing a comprehensive Python-based solution for generating high-precision Portuguese subtitles from English audio in video files. This system combines state-of-the-art speech recognition (WhisperX/Faster-Whisper) with professional translation services (DeepL/Google Translate) to create accurately synchronized, professionally formatted Portuguese subtitles.

## Core Objectives
1. Extract and transcribe English audio with maximum accuracy and precise timestamps
2. Translate English transcriptions to Portuguese while preserving context and meaning
3. Generate properly formatted, synchronized SRT subtitle files
4. Optimize for both accuracy and processing efficiency

## Implementation Architecture

### Phase 1: Environment Setup

```bash
# Create project structure
mkdir english-to-portuguese-subtitles
cd english-to-portuguese-subtitles
mkdir src output temp logs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install git+https://github.com/m-bain/whisperx.git
pip install faster-whisper
pip install deep-translator googletrans==4.0.0rc1
pip install srt moviepy ffmpeg-python
pip install pandas numpy tqdm
```

### Phase 2: System Requirements Validation

```python
# requirements_check.py
import sys
import torch
import subprocess

def check_system_requirements():
    """Validate system meets minimum requirements"""
    
    checks = {
        "Python Version": sys.version,
        "CUDA Available": torch.cuda.is_available(),
        "GPU Device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU Only",
        "VRAM Available": f"{torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB" if torch.cuda.is_available() else "N/A",
        "FFmpeg Installed": subprocess.run(['ffmpeg', '-version'], capture_output=True).returncode == 0
    }
    
    for check, result in checks.items():
        print(f"{check}: {result}")
    
    # Recommend configuration based on available resources
    if torch.cuda.is_available():
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        if vram >= 10:
            print("\nRecommended: WhisperX with large-v3 model")
        elif vram >= 6:
            print("\nRecommended: WhisperX with medium model or Faster-Whisper with large-v3")
        else:
            print("\nRecommended: Faster-Whisper with small/medium model using int8 quantization")
    else:
        print("\nCPU-only mode: Use Faster-Whisper with tiny/base model")

if __name__ == "__main__":
    check_system_requirements()
```

### Phase 3: Main Implementation

```python
# subtitle_generator.py

import os
import gc
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import timedelta
import tempfile
import subprocess

import torch
import whisperx
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator, DeeplTranslator
import srt
import ffmpeg
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/subtitle_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SubtitleConfig:
    """Configuration for subtitle generation"""
    model_size: str = "large-v3"  # tiny, base, small, medium, large, large-v2, large-v3
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type: str = "float16" if torch.cuda.is_available() else "int8"
    batch_size: int = 16
    beam_size: int = 5
    
    # Translation settings
    translator: str = "google"  # google, deepl
    deepl_api_key: Optional[str] = None
    target_language: str = "pt"  # pt for Portuguese, pt-BR for Brazilian Portuguese
    
    # Subtitle formatting
    max_line_length: int = 42
    max_lines: int = 2
    max_duration: float = 7.0
    min_duration: float = 1.0
    reading_speed: int = 20  # characters per second
    
    # VAD settings
    use_vad: bool = True
    vad_min_silence_ms: int = 500
    vad_speech_pad_ms: int = 400
    
    # Output settings
    output_format: str = "srt"  # srt, vtt, txt
    include_timestamps: bool = True
    preserve_formatting: bool = True

class EnglishToPortugueseSubtitleGenerator:
    """
    Professional subtitle generation system for English to Portuguese translation
    """
    
    def __init__(self, config: SubtitleConfig):
        self.config = config
        self.model = None
        self.translator = None
        self._initialize_translator()
        
    def _initialize_translator(self):
        """Initialize the translation service"""
        if self.config.translator == "deepl" and self.config.deepl_api_key:
            logger.info("Initializing DeepL translator")
            self.translator = DeeplTranslator(
                api_key=self.config.deepl_api_key,
                source="en",
                target=self.config.target_language,
                use_free_api=True
            )
        else:
            logger.info("Initializing Google Translator")
            self.translator = GoogleTranslator(
                source='en',
                target=self.config.target_language
            )
    
    def extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file with optimal settings for Whisper
        """
        logger.info(f"Extracting audio from {video_path}")
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Use ffmpeg-python for better control
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                acodec='pcm_s16le',
                ar='16000',
                ac=1,
                loglevel='error'
            )
            ffmpeg.run(stream, overwrite_output=True)
            
            logger.info(f"Audio extracted successfully to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise
    
    def transcribe_with_whisperx(self, audio_path: str) -> Dict:
        """
        Use WhisperX for high-accuracy transcription with word-level timestamps
        """
        logger.info(f"Starting WhisperX transcription with model {self.config.model_size}")
        
        # Load model
        model = whisperx.load_model(
            self.config.model_size,
            self.config.device,
            compute_type=self.config.compute_type,
            language="en"
        )
        
        # Load and transcribe audio
        audio = whisperx.load_audio(audio_path)
        
        result = model.transcribe(
            audio,
            batch_size=self.config.batch_size,
            language="en",
            task="transcribe",
            chunk_length=30,  # Process in 30-second chunks
            print_progress=True
        )
        
        # Align for accurate word timestamps
        logger.info("Aligning transcription for word-level timestamps")
        model_a, metadata = whisperx.load_align_model(
            language_code="en",
            device=self.config.device
        )
        
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            self.config.device,
            return_char_alignments=False
        )
        
        # Clean up memory
        del model, model_a
        gc.collect()
        if self.config.device == "cuda":
            torch.cuda.empty_cache()
        
        logger.info(f"Transcription complete: {len(result['segments'])} segments")
        return result
    
    def transcribe_with_faster_whisper(self, audio_path: str) -> List[Dict]:
        """
        Alternative: Use Faster-Whisper for lower memory usage
        """
        logger.info(f"Starting Faster-Whisper transcription with model {self.config.model_size}")
        
        model = WhisperModel(
            self.config.model_size,
            device=self.config.device,
            compute_type=self.config.compute_type
        )
        
        segments, info = model.transcribe(
            audio_path,
            language="en",
            task="transcribe",
            beam_size=self.config.beam_size,
            word_timestamps=True,
            vad_filter=self.config.use_vad,
            vad_parameters={
                "min_silence_duration_ms": self.config.vad_min_silence_ms,
                "speech_pad_ms": self.config.vad_speech_pad_ms
            } if self.config.use_vad else None,
            condition_on_previous_text=False,  # Reduces hallucinations
            temperature=0.0,  # More deterministic
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6
        )
        
        # Convert to standard format
        result_segments = []
        for segment in segments:
            result_segments.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip(),
                'words': [
                    {
                        'word': word.word,
                        'start': word.start,
                        'end': word.end
                    } for word in segment.words
                ] if segment.words else []
            })
        
        logger.info(f"Transcription complete: {len(result_segments)} segments")
        return {'segments': result_segments}
    
    def translate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Translate English segments to Portuguese with context preservation
        """
        logger.info(f"Translating {len(segments)} segments to Portuguese")
        
        translated_segments = []
        
        # Group segments for context-aware translation
        text_buffer = []
        segment_indices = []
        
        for i, segment in enumerate(tqdm(segments, desc="Translating")):
            text = segment['text'].strip()
            
            if not text:
                continue
            
            # Collect segments for batch translation (better context)
            text_buffer.append(text)
            segment_indices.append(i)
            
            # Translate in batches of 5 for context
            if len(text_buffer) >= 5 or i == len(segments) - 1:
                # Join with special delimiter to preserve sentence boundaries
                combined_text = " [SEP] ".join(text_buffer)
                
                try:
                    # Translate with context
                    translated = self.translator.translate(combined_text)
                    
                    # Split back into segments
                    translated_parts = translated.split(" [SEP] ")
                    
                    # Handle case where translation doesn't preserve separators
                    if len(translated_parts) != len(text_buffer):
                        # Fallback to individual translation
                        translated_parts = [
                            self.translator.translate(text) 
                            for text in text_buffer
                        ]
                    
                    # Create translated segments
                    for idx, trans_text in zip(segment_indices, translated_parts):
                        translated_segment = segments[idx].copy()
                        translated_segment['text'] = trans_text.strip()
                        translated_segment['original_text'] = segments[idx]['text']
                        translated_segments.append(translated_segment)
                    
                except Exception as e:
                    logger.error(f"Translation error: {e}")
                    # Fallback to individual translation
                    for idx in segment_indices:
                        try:
                            trans_text = self.translator.translate(segments[idx]['text'])
                            translated_segment = segments[idx].copy()
                            translated_segment['text'] = trans_text
                            translated_segment['original_text'] = segments[idx]['text']
                            translated_segments.append(translated_segment)
                        except:
                            # Keep original if translation fails
                            translated_segments.append(segments[idx])
                
                # Clear buffers
                text_buffer = []
                segment_indices = []
        
        logger.info(f"Translation complete: {len(translated_segments)} segments")
        return translated_segments
    
    def optimize_subtitles(self, segments: List[Dict]) -> List[Dict]:
        """
        Optimize subtitles for readability and synchronization
        """
        logger.info("Optimizing subtitles for readability")
        
        optimized = []
        
        for segment in segments:
            text = segment['text'].strip()
            duration = segment['end'] - segment['start']
            
            # Check if optimization needed
            chars_per_second = len(text) / duration if duration > 0 else 0
            needs_split = (
                len(text) > self.config.max_line_length * self.config.max_lines or
                duration > self.config.max_duration or
                chars_per_second > self.config.reading_speed
            )
            
            if needs_split and len(text.split()) > 1:
                # Smart splitting based on punctuation and length
                split_segments = self._split_segment(segment)
                optimized.extend(split_segments)
            else:
                # Format text for display
                formatted_text = self._format_subtitle_text(text)
                segment['text'] = formatted_text
                optimized.append(segment)
        
        # Merge very short segments
        optimized = self._merge_short_segments(optimized)
        
        # Ensure no overlapping timestamps
        optimized = self._fix_overlapping_timestamps(optimized)
        
        logger.info(f"Optimization complete: {len(optimized)} final segments")
        return optimized
    
    def _split_segment(self, segment: Dict) -> List[Dict]:
        """
        Intelligently split long segments
        """
        text = segment['text']
        duration = segment['end'] - segment['start']
        words = text.split()
        
        # Try to split at punctuation first
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        if len(sentences) > 1:
            # Split by sentences
            segments = []
            time_per_char = duration / len(text)
            current_time = segment['start']
            
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    sentence_duration = len(sentence) * time_per_char
                    segments.append({
                        'start': current_time,
                        'end': current_time + sentence_duration,
                        'text': self._format_subtitle_text(sentence)
                    })
                    current_time += sentence_duration
            
            return segments
        
        # Fall back to word-based splitting
        segments = []
        words_per_segment = len(words) // 2
        
        for i in range(0, len(words), words_per_segment):
            chunk_words = words[i:i + words_per_segment]
            chunk_text = ' '.join(chunk_words)
            
            # Calculate proportional timing
            start_ratio = i / len(words)
            end_ratio = min((i + len(chunk_words)) / len(words), 1.0)
            
            segments.append({
                'start': segment['start'] + (duration * start_ratio),
                'end': segment['start'] + (duration * end_ratio),
                'text': self._format_subtitle_text(chunk_text)
            })
        
        return segments
    
    def _format_subtitle_text(self, text: str) -> str:
        """
        Format text for subtitle display (line breaks, length limits)
        """
        words = text.split()
        
        if len(text) <= self.config.max_line_length:
            return text
        
        # Try to split into two balanced lines
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) <= self.config.max_line_length:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                
                if len(lines) >= self.config.max_lines:
                    break
        
        if current_line and len(lines) < self.config.max_lines:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines[:self.config.max_lines])
    
    def _merge_short_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Merge segments that are too short
        """
        if not segments:
            return segments
        
        merged = []
        buffer = None
        
        for segment in segments:
            duration = segment['end'] - segment['start']
            
            if duration < self.config.min_duration and buffer:
                # Merge with previous
                buffer['end'] = segment['end']
                buffer['text'] = buffer['text'] + ' ' + segment['text']
            else:
                if buffer:
                    merged.append(buffer)
                buffer = segment.copy()
        
        if buffer:
            merged.append(buffer)
        
        return merged
    
    def _fix_overlapping_timestamps(self, segments: List[Dict]) -> List[Dict]:
        """
        Ensure no timestamp overlaps
        """
        for i in range(1, len(segments)):
            if segments[i]['start'] < segments[i-1]['end']:
                # Adjust timestamps to prevent overlap
                gap = 0.1  # 100ms gap
                segments[i]['start'] = segments[i-1]['end'] + gap
        
        return segments
    
    def create_srt_file(self, segments: List[Dict], output_path: str):
        """
        Generate SRT subtitle file
        """
        logger.info(f"Creating SRT file: {output_path}")
        
        srt_segments = []
        
        for i, segment in enumerate(segments, 1):
            srt_segment = srt.Subtitle(
                index=i,
                start=timedelta(seconds=segment['start']),
                end=timedelta(seconds=segment['end']),
                content=segment['text']
            )
            srt_segments.append(srt_segment)
        
        # Write SRT file with proper encoding
        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.write(srt.compose(srt_segments))
        
        logger.info(f"SRT file created successfully: {output_path}")
    
    def create_vtt_file(self, segments: List[Dict], output_path: str):
        """
        Generate WebVTT subtitle file
        """
        logger.info(f"Creating VTT file: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for i, segment in enumerate(segments, 1):
                start = self._format_vtt_timestamp(segment['start'])
                end = self._format_vtt_timestamp(segment['end'])
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{segment['text']}\n\n")
        
        logger.info(f"VTT file created successfully: {output_path}")
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """Format timestamp for VTT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def process_video(
        self,
        video_path: str,
        output_path: str,
        use_whisperx: bool = True,
        save_intermediate: bool = False
    ) -> Dict:
        """
        Main processing pipeline
        """
        logger.info(f"Starting subtitle generation for: {video_path}")
        
        # Validate input
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        audio_path = None
        results = {
            'video_path': video_path,
            'output_path': output_path,
            'segments': [],
            'statistics': {}
        }
        
        try:
            # Step 1: Extract audio
            audio_path = self.extract_audio(video_path)
            
            # Step 2: Transcribe
            if use_whisperx and self.config.device == "cuda":
                transcription = self.transcribe_with_whisperx(audio_path)
            else:
                transcription = self.transcribe_with_faster_whisper(audio_path)
            
            segments = transcription['segments']
            results['statistics']['original_segments'] = len(segments)
            
            # Save intermediate transcription if requested
            if save_intermediate:
                intermediate_path = output_path.replace('.srt', '_english.srt')
                self.create_srt_file(segments, intermediate_path)
                results['intermediate_file'] = intermediate_path
            
            # Step 3: Translate
            translated_segments = self.translate_segments(segments)
            results['statistics']['translated_segments'] = len(translated_segments)
            
            # Step 4: Optimize
            optimized_segments = self.optimize_subtitles(translated_segments)
            results['statistics']['final_segments'] = len(optimized_segments)
            results['segments'] = optimized_segments
            
            # Step 5: Create output file
            if self.config.output_format == "srt":
                self.create_srt_file(optimized_segments, output_path)
            elif self.config.output_format == "vtt":
                self.create_vtt_file(optimized_segments, output_path)
            
            # Calculate statistics
            total_duration = optimized_segments[-1]['end'] if optimized_segments else 0
            results['statistics']['total_duration'] = total_duration
            results['statistics']['average_segment_duration'] = (
                total_duration / len(optimized_segments) if optimized_segments else 0
            )
            
            logger.info("Subtitle generation completed successfully")
            
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            results['error'] = str(e)
            raise
            
        finally:
            # Cleanup temporary audio file
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
                logger.info("Temporary audio file cleaned up")
        
        return results

class BatchProcessor:
    """
    Process multiple videos in batch
    """
    
    def __init__(self, config: SubtitleConfig):
        self.config = config
        self.generator = EnglishToPortugueseSubtitleGenerator(config)
    
    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        video_extensions: List[str] = ['.mp4', '.avi', '.mkv', '.mov']
    ):
        """
        Process all videos in a directory
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all video files
        video_files = []
        for ext in video_extensions:
            video_files.extend(input_path.glob(f"*{ext}"))
            video_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        logger.info(f"Found {len(video_files)} video files to process")
        
        results = []
        for video_file in tqdm(video_files, desc="Processing videos"):
            output_file = output_path / f"{video_file.stem}_portuguese.srt"
            
            try:
                result = self.generator.process_video(
                    str(video_file),
                    str(output_file),
                    use_whisperx=True,
                    save_intermediate=True
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to process {video_file}: {e}")
                results.append({
                    'video_path': str(video_file),
                    'error': str(e)
                })
        
        # Save batch results
        results_file = output_path / "batch_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Batch processing complete. Results saved to {results_file}")
        return results

# Main execution script
def main():
    """
    Main entry point for the subtitle generation system
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate Portuguese subtitles from English videos"
    )
    parser.add_argument(
        "input",
        help="Input video file or directory"
    )
    parser.add_argument(
        "output",
        help="Output subtitle file or directory"
    )
    parser.add_argument(
        "--model",
        default="large-v3",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="Whisper model size"
    )
    parser.add_argument(
        "--translator",
        default="google",
        choices=["google", "deepl"],
        help="Translation service"
    )
    parser.add_argument(
        "--deepl-api-key",
        help="DeepL API key (required for DeepL translation)"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process directory of videos"
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Processing device"
    )
    parser.add_argument(
        "--save-intermediate",
        action="store_true",
        help="Save English transcription"
    )
    parser.add_argument(
        "--target-language",
        default="pt",
        choices=["pt", "pt-BR"],
        help="Portuguese variant (pt=European, pt-BR=Brazilian)"
    )
    
    args = parser.parse_args()
    
    # Configure system
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    
    config = SubtitleConfig(
        model_size=args.model,
        device=device,
        translator=args.translator,
        deepl_api_key=args.deepl_api_key,
        target_language=args.target_language
    )
    
    # Process based on mode
    if args.batch:
        processor = BatchProcessor(config)
        processor.process_directory(args.input, args.output)
    else:
        generator = EnglishToPortugueseSubtitleGenerator(config)
        generator.process_video(
            args.input,
            args.output,
            use_whisperx=(device == "cuda"),
            save_intermediate=args.save_intermediate
        )

if __name__ == "__main__":
    main()
```

### Phase 4: Testing and Validation

```python
# test_subtitle_quality.py

import difflib
from typing import List, Dict
import srt
import statistics

class SubtitleQualityAnalyzer:
    """
    Analyze and validate subtitle quality
    """
    
    @staticmethod
    def analyze_srt_file(srt_path: str) -> Dict:
        """
        Analyze SRT file for quality metrics
        """
        with open(srt_path, 'r', encoding='utf-8') as f:
            subtitles = list(srt.parse(f.read()))
        
        metrics = {
            'total_subtitles': len(subtitles),
            'total_duration': 0,
            'average_duration': 0,
            'average_cps': 0,  # Characters per second
            'max_line_length': 0,
            'overlapping_count': 0,
            'gap_issues': 0,
            'reading_speed_issues': 0
        }
        
        durations = []
        cps_values = []
        
        for i, sub in enumerate(subtitles):
            duration = (sub.end - sub.start).total_seconds()
            durations.append(duration)
            
            # Character per second
            if duration > 0:
                cps = len(sub.content) / duration
                cps_values.append(cps)
                
                # Check reading speed (>20 CPS is too fast)
                if cps > 20:
                    metrics['reading_speed_issues'] += 1
            
            # Check line length
            for line in sub.content.split('\n'):
                metrics['max_line_length'] = max(
                    metrics['max_line_length'],
                    len(line)
                )
            
            # Check for overlaps
            if i > 0:
                prev_sub = subtitles[i-1]
                if sub.start < prev_sub.end:
                    metrics['overlapping_count'] += 1
                
                # Check gaps (>2 seconds might be an issue)
                gap = (sub.start - prev_sub.end).total_seconds()
                if gap > 2:
                    metrics['gap_issues'] += 1
        
        metrics['total_duration'] = sum(durations)
        metrics['average_duration'] = statistics.mean(durations) if durations else 0
        metrics['average_cps'] = statistics.mean(cps_values) if cps_values else 0
        
        return metrics
    
    @staticmethod
    def compare_translations(
        original_srt: str,
        translated_srt: str
    ) -> Dict:
        """
        Compare original and translated subtitles
        """
        with open(original_srt, 'r', encoding='utf-8') as f:
            original = list(srt.parse(f.read()))
        
        with open(translated_srt, 'r', encoding='utf-8') as f:
            translated = list(srt.parse(f.read()))
        
        comparison = {
            'segment_count_match': len(original) == len(translated),
            'original_count': len(original),
            'translated_count': len(translated),
            'timing_differences': [],
            'length_ratio': []
        }
        
        for orig, trans in zip(original, translated):
            # Check timing preservation
            time_diff = abs(
                (orig.start - trans.start).total_seconds()
            )
            comparison['timing_differences'].append(time_diff)
            
            # Check text length ratio
            if len(orig.content) > 0:
                ratio = len(trans.content) / len(orig.content)
                comparison['length_ratio'].append(ratio)
        
        comparison['avg_timing_diff'] = statistics.mean(
            comparison['timing_differences']
        ) if comparison['timing_differences'] else 0
        
        comparison['avg_length_ratio'] = statistics.mean(
            comparison['length_ratio']
        ) if comparison['length_ratio'] else 0
        
        return comparison

# Run quality check
if __name__ == "__main__":
    analyzer = SubtitleQualityAnalyzer()
    
    # Analyze generated subtitles
    metrics = analyzer.analyze_srt_file("output/video_portuguese.srt")
    print("Quality Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Compare with original if available
    if os.path.exists("output/video_english.srt"):
        comparison = analyzer.compare_translations(
            "output/video_english.srt",
            "output/video_portuguese.srt"
        )
        print("\nTranslation Comparison:")
        for key, value in comparison.items():
            if not isinstance(value, list):
                print(f"  {key}: {value}")
```

## Usage Instructions

### Basic Usage

```bash
# Single video processing
python subtitle_generator.py video.mp4 video_portuguese.srt

# With specific model
python subtitle_generator.py video.mp4 output.srt --model large-v3

# Using DeepL for translation
python subtitle_generator.py video.mp4 output.srt --translator deepl --deepl-api-key YOUR_KEY

# Batch processing
python subtitle_generator.py input_folder/ output_folder/ --batch

# Save intermediate English subtitles
python subtitle_generator.py video.mp4 output.srt --save-intermediate

# Brazilian Portuguese
python subtitle_generator.py video.mp4 output.srt --target-language pt-BR
```

### Advanced Configuration

```python
# custom_config.py
from subtitle_generator import SubtitleConfig, EnglishToPortugueseSubtitleGenerator

# Custom configuration for specific needs
config = SubtitleConfig(
    model_size="large-v3",
    device="cuda",
    compute_type="float16",
    batch_size=24,  # Increase for faster processing
    beam_size=10,   # Increase for better accuracy
    translator="deepl",
    deepl_api_key="your-api-key",
    target_language="pt-BR",
    max_line_length=37,  # Netflix standard
    max_duration=6.0,
    reading_speed=17,  # Slower reading speed
    use_vad=True,
    vad_min_silence_ms=300  # More sensitive to speech
)

generator = EnglishToPortugueseSubtitleGenerator(config)
result = generator.process_video(
    "input_video.mp4",
    "output_subtitles.srt",
    use_whisperx=True,
    save_intermediate=True
)

print(f"Generated {result['statistics']['final_segments']} subtitles")
```

## Performance Optimization Guide

### GPU Memory Management

```python
# For different GPU memory sizes:

# 4GB VRAM
config_4gb = SubtitleConfig(
    model_size="small",
    compute_type="int8",
    batch_size=4
)

# 8GB VRAM
config_8gb = SubtitleConfig(
    model_size="medium",
    compute_type="int8_float16",
    batch_size=8
)

# 12GB+ VRAM
config_12gb = SubtitleConfig(
    model_size="large-v3",
    compute_type="float16",
    batch_size=16
)
```

### CPU-Only Processing

```python
# Optimized for CPU
config_cpu = SubtitleConfig(
    model_size="base",
    device="cpu",
    compute_type="int8",
    batch_size=1,
    beam_size=1  # Faster but less accurate
)
```

## Quality Assurance Checklist

1. **Pre-processing Validation**
   - [ ] Video file exists and is readable
   - [ ] Audio track is present
   - [ ] Sufficient disk space for temporary files

2. **Transcription Quality**
   - [ ] Model size appropriate for available resources
   - [ ] VAD enabled to reduce hallucinations
   - [ ] Beam size ≥ 5 for better accuracy

3. **Translation Quality**
   - [ ] Context-aware translation (batch processing)
   - [ ] Proper handling of technical terms
   - [ ] Preservation of punctuation and formatting

4. **Subtitle Formatting**
   - [ ] Line length ≤ 42 characters
   - [ ] Reading speed ≤ 20 CPS
   - [ ] No overlapping timestamps
   - [ ] Proper UTF-8 encoding

5. **Post-processing Validation**
   - [ ] All segments have valid timestamps
   - [ ] Text is properly formatted
   - [ ] File is valid SRT/VTT format

## Troubleshooting Guide

### Common Issues and Solutions

1. **Out of Memory (OOM) Error**
   ```python
   # Reduce batch size or model size
   config.batch_size = 4
   config.model_size = "medium"
   ```

2. **Slow Processing**
   ```python
   # Use faster-whisper instead of whisperx
   use_whisperx = False
   # Or use smaller model
   config.model_size = "small"
   ```

3. **Translation API Limits**
   ```python
   # Implement rate limiting
   import time
   time.sleep(0.1)  # Between translation calls
   ```

4. **Poor Transcription Quality**
   ```python
   # Increase beam size and use VAD
   config.beam_size = 10
   config.use_vad = True
   ```

## Expected Performance Metrics

- **WhisperX with large-v3**: ~70x real-time on GPU
- **Faster-Whisper with large-v3**: ~10-15x real-time on GPU
- **Translation**: ~100-200 segments per minute
- **Total processing**: ~5-10 minutes for 1-hour video on GPU

## Final Notes

This system provides professional-grade English to Portuguese subtitle generation with:
- State-of-the-art accuracy using Whisper models
- Context-aware translation
- Proper subtitle formatting and timing
- Batch processing capabilities
- Comprehensive error handling and logging

The implementation is production-ready and can be integrated into larger video processing pipelines or used as a standalone tool for content localization.
