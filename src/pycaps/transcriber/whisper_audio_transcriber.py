from .base_transcriber import AudioTranscriber
from .anti_hallucination_config import AntiHallucinationConfig, PresetConfigs
from typing import Optional, Any, List, Tuple, Union
from pycaps.common import Document, Segment, Line, Word, TimeFragment
from pycaps.logger import logger
import re
import librosa
import numpy as np
import tempfile
import os
from pathlib import Path

class WhisperAudioTranscriber(AudioTranscriber):
    def __init__(self, model_size: str = "medium", language: Optional[str] = None, model: Optional[Any] = None, 
                 initial_prompt: Optional[str] = None, portuguese_vocabulary: Optional[List[str]] = None,
                 anti_hallucination_config: Optional[Union[AntiHallucinationConfig, str]] = None,
                 # Legacy parameters for backward compatibility
                 enable_vad: Optional[bool] = None, chunk_length: Optional[int] = None, 
                 overlap: Optional[int] = None, adaptive_thresholds: Optional[bool] = None):
        """
        Transcribes audio using OpenAI's Whisper model with Portuguese optimizations
        and anti-hallucination features for long videos.

        Args:
            model_size: Size of the Whisper model to use (e.g., "tiny", "base", "medium").
            language: Language of the audio (e.g., "en", "pt").
            model: (Optional) A pre-loaded Whisper model instance. If provided, model_size is ignored.
            initial_prompt: Custom prompt to guide transcription (max 244 tokens).
            portuguese_vocabulary: List of Portuguese compound/religious terms to recognize.
            anti_hallucination_config: Configuration for anti-hallucination features. Can be:
                - AntiHallucinationConfig object
                - String preset: "maximum_quality", "balanced", "fast_processing", "podcasts", "short_videos"
                - None (uses duration-based auto configuration)
            
            Legacy parameters (deprecated, use anti_hallucination_config instead):
            enable_vad: Enable Voice Activity Detection preprocessing for long videos.
            chunk_length: Length of audio chunks in seconds for long video processing.
            overlap: Overlap between chunks in seconds.
            adaptive_thresholds: Use adaptive thresholds based on audio duration.
        """
        self._model_size = model_size
        self._language = language
        self._model = model
        self._initial_prompt = initial_prompt
        self._portuguese_vocabulary = portuguese_vocabulary or []
        self._vad_model = None
        
        # Handle anti-hallucination configuration
        self._config = self._initialize_config(
            anti_hallucination_config, enable_vad, chunk_length, overlap, adaptive_thresholds
        )

    def _initialize_config(self, config: Optional[Union[AntiHallucinationConfig, str]], 
                          enable_vad: Optional[bool], chunk_length: Optional[int], 
                          overlap: Optional[int], adaptive_thresholds: Optional[bool]) -> AntiHallucinationConfig:
        """Initialize anti-hallucination configuration."""
        
        # If config is provided as string (preset)
        if isinstance(config, str):
            preset_map = {
                "maximum_quality": PresetConfigs.maximum_quality,
                "balanced": PresetConfigs.balanced,
                "fast_processing": PresetConfigs.fast_processing,
                "podcasts": PresetConfigs.podcasts,
                "short_videos": PresetConfigs.short_videos,
            }
            
            if config in preset_map:
                return preset_map[config]()
            else:
                logger().warning(f"Unknown preset '{config}', using balanced configuration")
                return PresetConfigs.balanced()
        
        # If config is provided as object
        elif isinstance(config, AntiHallucinationConfig):
            self._custom_config_provided = True
            return config
        
        # If no config provided, but legacy parameters are given
        elif any(param is not None for param in [enable_vad, chunk_length, overlap, adaptive_thresholds]):
            logger().info("Using legacy parameters for anti-hallucination configuration")
            base_config = PresetConfigs.balanced()
            
            # Override with legacy parameters
            if enable_vad is not None:
                base_config.enable_vad = enable_vad
            if chunk_length is not None:
                base_config.chunk_length = chunk_length
            if overlap is not None:
                base_config.overlap = overlap
            if adaptive_thresholds is not None:
                base_config.adaptive_thresholds = adaptive_thresholds
            
            return base_config
        
        # Default: use duration-based auto configuration (will be set in transcribe method)
        else:
            return PresetConfigs.balanced()

    def _build_portuguese_prompt(self) -> str:
        """Build optimized prompt for Portuguese compound and religious terms."""
        base_prompt = "Transcrição em português brasileiro."
        
        # Common religious/biblical vocabulary that gets misrecognized
        religious_terms = [
            "Getsêmani", "ajoelhou-se", "prostrou-se", "Jerusalém", "bem-aventurança",
            "auto-sacrifício", "cruz-sagrada", "pós-ressurreição", "ressuscitou",
            "anti-cristo", "sub-reino", "sobre-humano", "bendisse-o", "chamou-se"
        ]
        
        # Add user-provided vocabulary
        all_terms = religious_terms + self._portuguese_vocabulary
        
        if all_terms:
            # Format as examples in the prompt
            examples = ", ".join(all_terms[:15])  # Limit to stay under 244 tokens
            vocabulary_prompt = f" Vocabulário: {examples}."
            
            # Ensure we stay under 244 token limit
            full_prompt = base_prompt + vocabulary_prompt
            if len(full_prompt.split()) > 200:  # Conservative token estimate
                full_prompt = base_prompt + f" Vocabulário: {', '.join(all_terms[:8])}."
                
            return full_prompt
        
        return base_prompt

    def _get_vad_model(self):
        """Load Silero VAD model for voice activity detection."""
        if self._vad_model is None:
            try:
                import torch
                torch.set_num_threads(1)  # Optimize for single-threaded use
                
                # Try to load Silero VAD model
                model, utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False,
                    onnx=False
                )
                self._vad_model = model
                self._vad_utils = utils
                logger().debug("Silero VAD model loaded successfully")
            except Exception as e:
                logger().warning(f"Failed to load VAD model: {e}. Falling back to energy-based VAD.")
                self._vad_model = "energy"  # Fallback to simple energy-based VAD
        
        return self._vad_model

    def _detect_speech_segments_vad(self, audio_path: str) -> List[Tuple[float, float]]:
        """Detect speech segments using VAD to avoid transcribing silence/noise."""
        try:
            vad_model = self._get_vad_model()
            
            if vad_model == "energy":
                return self._detect_speech_segments_energy(audio_path)
            
            # Load audio for VAD
            audio, sample_rate = librosa.load(audio_path, sr=16000)
            
            # Silero VAD expects specific sample rate
            if sample_rate != 16000:
                audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
                sample_rate = 16000
            
            # Convert to tensor
            import torch
            audio_tensor = torch.from_numpy(audio).float()
            
            # Get speech timestamps
            speech_timestamps = self._vad_utils[0](
                audio_tensor, vad_model, sampling_rate=sample_rate
            )
            
            # Convert to time segments
            segments = []
            for timestamp in speech_timestamps:
                start_time = timestamp['start'] / sample_rate
                end_time = timestamp['end'] / sample_rate
                
                # Merge very close segments (within 0.5 seconds)
                if segments and start_time - segments[-1][1] < 0.5:
                    segments[-1] = (segments[-1][0], end_time)
                else:
                    segments.append((start_time, end_time))
            
            logger().debug(f"VAD detected {len(segments)} speech segments")
            return segments
            
        except Exception as e:
            logger().warning(f"VAD processing failed: {e}. Using energy-based fallback.")
            return self._detect_speech_segments_energy(audio_path)

    def _detect_speech_segments_energy(self, audio_path: str) -> List[Tuple[float, float]]:
        """Fallback energy-based speech detection."""
        try:
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Calculate energy in short windows
            hop_length = int(0.1 * sr)  # 100ms windows
            energy = np.array([
                np.sum(audio[i:i+hop_length]**2) 
                for i in range(0, len(audio)-hop_length, hop_length)
            ])
            
            # Adaptive threshold based on energy distribution
            energy_threshold = np.percentile(energy, 30)
            
            # Find speech segments
            speech_frames = energy > energy_threshold
            segments = []
            
            start = None
            for i, is_speech in enumerate(speech_frames):
                time = i * hop_length / sr
                
                if is_speech and start is None:
                    start = time
                elif not is_speech and start is not None:
                    segments.append((start, time))
                    start = None
            
            # Close final segment if needed
            if start is not None:
                segments.append((start, len(audio) / sr))
            
            # Merge close segments and filter short ones
            merged_segments = []
            for start, end in segments:
                if end - start < 0.3:  # Skip very short segments
                    continue
                    
                if merged_segments and start - merged_segments[-1][1] < 1.0:
                    merged_segments[-1] = (merged_segments[-1][0], end)
                else:
                    merged_segments.append((start, end))
            
            logger().debug(f"Energy-based VAD detected {len(merged_segments)} speech segments")
            return merged_segments
            
        except Exception as e:
            logger().error(f"Energy-based VAD failed: {e}")
            # Return full audio as single segment if all fails
            duration = librosa.get_duration(path=audio_path)
            return [(0.0, duration)]

    def _extract_audio_segment(self, audio_path: str, start: float, end: float) -> str:
        """Extract audio segment and save to temporary file."""
        try:
            audio, sr = librosa.load(audio_path, sr=None, offset=start, duration=end-start)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp_file.name
            temp_file.close()
            
            # Save segment
            import soundfile as sf
            sf.write(temp_path, audio, sr)
            
            return temp_path
            
        except Exception as e:
            logger().error(f"Failed to extract audio segment: {e}")
            raise


    def _post_process_portuguese_compounds(self, document: Document) -> Document:
        """Post-process document to fix Portuguese compound word splitting."""
        # Common Portuguese compound word patterns
        compound_patterns = {
            # Reflexive verbs - most common issue
            r'\b(\w+)\s+se\b': r'\1-se',
            r'\b(\w+)\s+me\b': r'\1-me', 
            r'\b(\w+)\s+te\b': r'\1-te',
            r'\b(\w+)\s+nos\b': r'\1-nos',
            r'\b(\w+)\s+lhe\b': r'\1-lhe',
            r'\b(\w+)\s+lhes\b': r'\1-lhes',
            
            # Common prefixes split incorrectly
            r'\bbem\s+(\w+)': r'bem-\1',
            r'\bmal\s+(\w+)': r'mal-\1',
            r'\bauto\s+(\w+)': r'auto-\1',
            r'\banti\s+(\w+)': r'anti-\1',
            r'\bpós\s+(\w+)': r'pós-\1',
            r'\bpré\s+(\w+)': r'pré-\1',
            r'\bsobre\s+(\w+)': r'sobre-\1',
            r'\bsub\s+(\w+)': r'sub-\1',
        }
        
        # Specific religious/biblical terms that get misrecognized
        religious_corrections = {
            "jet semany": "Getsêmani",
            "jet sê mani": "Getsêmani", 
            "get semany": "Getsêmani",
            "jets emany": "Getsêmani",
            "jet semani": "Getsêmani",
            "bem aventurança": "bem-aventurança",
            "bem aventurado": "bem-aventurado",
            "cruz sagrada": "cruz-sagrada",
            "pós ressurreição": "pós-ressurreição",
        }

        # Process each segment
        for segment in document.segments:
            for line in segment.lines:
                # Collect all words in the line for context processing
                words_text = [word.text for word in line.words]
                full_line_text = " ".join(words_text)
                
                # Apply religious/biblical corrections first (case insensitive)
                corrected_text = full_line_text
                for incorrect, correct in religious_corrections.items():
                    corrected_text = re.sub(re.escape(incorrect), correct, corrected_text, flags=re.IGNORECASE)
                
                # Apply compound word patterns
                for pattern, replacement in compound_patterns.items():
                    corrected_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)
                
                # If text changed, update words
                if corrected_text != full_line_text:
                    logger().debug(f"Portuguese correction: '{full_line_text}' -> '{corrected_text}'")
                    corrected_words = corrected_text.split()
                    
                    # Update word texts while preserving timing
                    for i, word in enumerate(line.words):
                        if i < len(corrected_words):
                            word.text = corrected_words[i]
        
        return document

    def transcribe(self, audio_path: str) -> Document:
        """
        Transcribes the audio file and returns segments with timestamps.
        Uses chunking and VAD for long videos to prevent hallucinations.
        """
        try:
            # Get audio duration and set up duration-based config if needed
            duration = librosa.get_duration(path=audio_path)
            
            # Use duration-based configuration if no specific config was provided
            if not hasattr(self, '_duration_config_applied') and not hasattr(self, '_custom_config_provided'):
                self._config = AntiHallucinationConfig.get_duration_based_config(duration)
                self._duration_config_applied = True
                logger().info(f"Using duration-based anti-hallucination config for {duration:.1f}s video")
                self._config.log_configuration(duration)
            
            # Check if we should use chunking for long videos
            if self._config.should_use_chunking(duration):
                logger().info("Using chunked transcription for long video to prevent hallucinations")
                return self._transcribe_chunked(audio_path)
            else:
                return self._transcribe_single(audio_path)
        
        except Exception as e:
            logger().error(f"Failed to get audio duration: {e}")
            # Fallback to single transcription
            return self._transcribe_single(audio_path)

    def _transcribe_chunked(self, audio_path: str) -> Document:
        """Transcribe long audio using overlapping chunks with VAD preprocessing."""
        try:
            # Get audio duration and adaptive thresholds
            duration = librosa.get_duration(path=audio_path)
            whisper_params = self._config.get_whisper_params(duration)
            
            logger().debug(f"Transcribing {duration:.1f}s audio with chunking. Thresholds: {whisper_params}")
            
            # Use VAD to detect speech segments if enabled
            if self._config.enable_vad:
                speech_segments = self._detect_speech_segments_vad(audio_path)
                logger().debug(f"VAD detected {len(speech_segments)} speech segments")
            else:
                # Use full duration if VAD disabled
                speech_segments = [(0.0, duration)]
            
            # Create chunks from speech segments
            chunks = self._create_chunks_from_speech_segments(speech_segments, duration)
            
            # Transcribe each chunk
            all_documents = []
            temp_files = []
            
            for i, (start, end) in enumerate(chunks):
                logger().debug(f"Processing chunk {i+1}/{len(chunks)}: {start:.1f}s - {end:.1f}s")
                
                # Extract audio segment
                chunk_path = self._extract_audio_segment(audio_path, start, end)
                temp_files.append(chunk_path)
                
                try:
                    # Transcribe chunk with adaptive thresholds
                    chunk_doc = self._transcribe_single(chunk_path, time_offset=start, **whisper_params)
                    all_documents.append(chunk_doc)
                except Exception as e:
                    logger().warning(f"Failed to transcribe chunk {i+1}: {e}")
                    continue
            
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
            
            # Merge documents with overlap deduplication
            return self._merge_chunked_documents(all_documents, chunks)
            
        except Exception as e:
            logger().warning(f"Chunked transcription failed: {e}. Falling back to single transcription.")
            return self._transcribe_single(audio_path)

    def _create_chunks_from_speech_segments(self, speech_segments: List[Tuple[float, float]], 
                                          total_duration: float) -> List[Tuple[float, float]]:
        """Create overlapping chunks from speech segments."""
        chunks = []
        
        if not speech_segments:
            # Fallback to time-based chunking
            current_start = 0
            while current_start < total_duration:
                chunk_end = min(current_start + self._config.chunk_length, total_duration)
                chunks.append((current_start, chunk_end))
                current_start += self._config.chunk_length - self._config.overlap
            return chunks
        
        # Create chunks that respect speech boundaries
        current_start = 0
        
        for start, end in speech_segments:
            # If there's a gap before this speech segment and we need to start a new chunk
            if start > current_start + self._config.chunk_length:
                # Create chunk up to previous speech
                if current_start < start:
                    chunks.append((current_start, min(current_start + self._config.chunk_length, start)))
                current_start = start
            
            # If this speech segment is very long, split it
            segment_start = max(current_start, start)
            while segment_start < end:
                chunk_end = min(segment_start + self._config.chunk_length, end, total_duration)
                chunks.append((segment_start, chunk_end))
                
                # Move to next chunk with overlap
                segment_start = chunk_end - self._config.overlap
                if segment_start >= chunk_end:
                    break
            
            current_start = max(current_start, end - self._config.overlap)
        
        # Handle remaining audio
        if current_start < total_duration:
            chunks.append((current_start, total_duration))
        
        return chunks

    def _transcribe_single(self, audio_path: str, time_offset: float = 0.0, **whisper_params) -> Document:
        """Transcribe a single audio file or chunk."""
        # Build appropriate prompt for Portuguese optimization
        prompt = self._initial_prompt
        if not prompt and (self._language == "pt" or not self._language):
            prompt = self._build_portuguese_prompt()
        
        # Get duration for adaptive thresholds if not provided
        if not whisper_params:
            try:
                duration = librosa.get_duration(path=audio_path)
                whisper_params = self._config.get_whisper_params(duration)
            except Exception:
                whisper_params = {
                    'compression_ratio_threshold': 2.4,
                    'logprob_threshold': -1.0,
                    'no_speech_threshold': 0.6
                }
        
        # Enhanced Whisper parameters for better accuracy and repetition prevention
        result = self._get_model(audio_path).transcribe(
            audio_path,
            word_timestamps=True,
            language=self._language,
            verbose=False,
            initial_prompt=prompt,
            temperature=0.0,  # More deterministic output
            condition_on_previous_text=False,  # Prevent repetition loops
            suppress_tokens=[-1],  # Suppress no speech token
            without_timestamps=False,
            **whisper_params
        )

        if "segments" not in result or not result["segments"]:
            logger().warning("Whisper returned no segments in the transcription.")
            return Document()

        logger().debug(f"Whisper result for chunk: {len(result['segments'])} segments")
        document = Document()
        
        for segment_info in result["segments"]:
            segment_start = float(segment_info["start"]) + time_offset
            segment_end = float(segment_info["end"]) + time_offset
            if segment_start == segment_end:
                segment_end = segment_start + 0.01
            segment_time = TimeFragment(start=segment_start, end=segment_end)
            segment = Segment(time=segment_time)
            line = Line(time=segment_time)
            segment.lines.add(line)

            if not "words" in segment_info or not isinstance(segment_info["words"], list):
                logger().debug(f"Segment '{segment_info['text']}' has no detailed word data.")
                continue

            for word_entry in segment_info["words"]:
                # Ensure 'word' is a string, sometimes Whisper might return non-string for certain symbols.
                word_text = str(word_entry["word"]).strip()
                if not word_text:
                    continue

                word_start = float(word_entry["start"]) + time_offset
                word_end = float(word_entry["end"]) + time_offset
                if word_start == word_end:
                    word_end = word_start + 0.01
                word_time = TimeFragment(start=word_start, end=word_end)
                word = Word(text=word_text, time=word_time)
                line.words.add(word)

            document.segments.add(segment)
        
        if not document.segments:
            logger().warning("No valid segments were processed from Whisper's transcription.")

        # Apply Portuguese post-processing if language is Portuguese or not specified
        if self._language == "pt" or not self._language:
            logger().debug("Applying Portuguese compound word post-processing...")
            document = self._post_process_portuguese_compounds(document)

        # Remove repetitive segments that Whisper sometimes generates
        logger().debug("Removing repetitive segments...")
        document = self._remove_repetitive_segments(document)

        return document

    def _merge_chunked_documents(self, documents: List[Document], chunks: List[Tuple[float, float]]) -> Document:
        """Merge chunked documents while handling overlaps."""
        if not documents:
            return Document()
        
        if len(documents) == 1:
            return documents[0]
        
        merged = Document()
        
        for i, doc in enumerate(documents):
            chunk_start, chunk_end = chunks[i]
            
            for segment in doc.segments:
                # For overlapping regions, only keep content from the first chunk that contains it
                segment_mid = (segment.time.start + segment.time.end) / 2
                
                # Check if this segment overlaps with previous chunks
                should_include = True
                if i > 0:
                    prev_chunk_start, prev_chunk_end = chunks[i-1]
                    overlap_start = max(chunk_start, prev_chunk_end - self._config.overlap)
                    
                    # If segment is in overlap region, check if it's closer to current chunk center
                    if overlap_start <= segment_mid <= chunk_start + self._config.overlap:
                        chunk_center = (chunk_start + chunk_end) / 2
                        prev_chunk_center = (prev_chunk_start + prev_chunk_end) / 2
                        
                        # Keep segment in chunk it's closer to center of
                        if abs(segment_mid - prev_chunk_center) <= abs(segment_mid - chunk_center):
                            should_include = False
                
                if should_include:
                    merged.segments.add(segment)
        
        # Sort segments by start time
        sorted_segments = sorted(merged.segments, key=lambda s: s.time.start)
        merged.segments.clear()
        for segment in sorted_segments:
            merged.segments.add(segment)
        
        logger().debug(f"Merged {len(documents)} chunks into {len(merged.segments)} segments")
        return merged

    def _remove_repetitive_segments(self, document: Document) -> Document:
        """Remove segments that contain excessive repetition with enhanced filtering."""
        if not document.segments:
            return document
        
        # Track patterns and their frequency
        segment_texts = []
        segment_compressions = []
        
        for segment in document.segments:
            text = ' '.join([word.text for line in segment.lines for word in line.words])
            segment_texts.append(text.strip())
            
            # Calculate compression ratio (text length vs expected length)
            words = text.split()
            expected_length = len(words) * 5  # Average word length estimate
            compression_ratio = len(text.encode('utf-8')) / max(expected_length, 1)
            segment_compressions.append(compression_ratio)
        
        to_remove = set()
        
        # 1. Check for exact repetition patterns (enhanced)
        for i in range(len(segment_texts) - 1):
            current_text = segment_texts[i]
            
            # Skip very short segments
            if len(current_text) < 5:
                continue
            
            # Count consecutive identical segments
            consecutive_count = 1
            j = i + 1
            while j < len(segment_texts) and segment_texts[j] == current_text:
                consecutive_count += 1
                j += 1
            
            # Remove excessive repetitions (keep first 2 max)
            if consecutive_count > 2:
                for k in range(i + 2, i + consecutive_count):
                    to_remove.add(k)
                logger().debug(f"Found {consecutive_count} consecutive identical segments: '{current_text[:50]}...'")
        
        # 2. Check for high compression ratio (likely hallucination)
        compression_threshold = 4.0  # Empirically determined
        for i, compression in enumerate(segment_compressions):
            if compression > compression_threshold and len(segment_texts[i]) > 20:
                to_remove.add(i)
                logger().debug(f"Removing high compression segment {i} (ratio: {compression:.2f}): '{segment_texts[i][:50]}...'")
        
        # 3. Check for semantic repetition (similar meaning)
        self._detect_semantic_repetition(segment_texts, to_remove)
        
        # 4. Check for specific repetitive phrases (existing logic enhanced)
        repetitive_phrases = [
            "E aí ele falou, ó, eu sou gay",
            "ele falou, ó, eu sou gay", 
            "aí ele falou, ó, eu sou gay",
            "você pode me ajudar",
            "muito obrigado",
            "por favor",
        ]
        
        for i, text in enumerate(segment_texts):
            for phrase in repetitive_phrases:
                if phrase.lower() in text.lower() and len(text) < len(phrase) + 15:
                    # Count occurrences across entire document
                    count = sum(1 for t in segment_texts if phrase.lower() in t.lower() and len(t) < len(phrase) + 15)
                    if count > 3:
                        # Keep only first 2 occurrences
                        occurrence_count = sum(1 for j in range(i) if phrase.lower() in segment_texts[j].lower() and len(segment_texts[j]) < len(phrase) + 15)
                        if occurrence_count >= 2:
                            to_remove.add(i)
                            logger().debug(f"Removing excessive repetitive phrase {i}: '{text[:50]}...'")
        
        # 5. Check for looping patterns (new)
        self._detect_looping_patterns(segment_texts, to_remove)
        
        # Create new document with filtered segments
        if to_remove:
            filtered_document = Document()
            for i, segment in enumerate(document.segments):
                if i not in to_remove:
                    filtered_document.segments.add(segment)
            
            logger().debug(f"Removed {len(to_remove)} problematic segments out of {len(document.segments)}")
            return filtered_document
        
        return document

    def _detect_semantic_repetition(self, segment_texts: List[str], to_remove: set):
        """Detect semantically similar segments that might be hallucinations."""
        from difflib import SequenceMatcher
        
        similarity_threshold = 0.8
        min_length = 20
        
        for i in range(len(segment_texts)):
            if i in to_remove or len(segment_texts[i]) < min_length:
                continue
                
            for j in range(i + 1, len(segment_texts)):
                if j in to_remove or len(segment_texts[j]) < min_length:
                    continue
                
                # Calculate similarity
                similarity = SequenceMatcher(None, segment_texts[i].lower(), segment_texts[j].lower()).ratio()
                
                if similarity > similarity_threshold:
                    # Keep the earlier segment, remove the later one
                    to_remove.add(j)
                    logger().debug(f"Removing semantically similar segment {j} (similarity: {similarity:.2f})")

    def _detect_looping_patterns(self, segment_texts: List[str], to_remove: set):
        """Detect looping patterns where the same sequence repeats."""
        min_pattern_length = 2
        max_pattern_length = 5
        
        for pattern_length in range(min_pattern_length, min(max_pattern_length + 1, len(segment_texts) // 3)):
            for start in range(len(segment_texts) - pattern_length * 3):
                if start in to_remove:
                    continue
                
                # Extract potential pattern
                pattern = segment_texts[start:start + pattern_length]
                
                # Check if this pattern repeats immediately after
                matches = 0
                pos = start + pattern_length
                
                while pos + pattern_length <= len(segment_texts):
                    candidate = segment_texts[pos:pos + pattern_length]
                    
                    # Check if candidate matches pattern (with some tolerance)
                    match_count = sum(1 for a, b in zip(pattern, candidate) if a.lower().strip() == b.lower().strip())
                    match_ratio = match_count / pattern_length
                    
                    if match_ratio >= 0.8:  # 80% match threshold
                        matches += 1
                        pos += pattern_length
                    else:
                        break
                
                # If pattern repeats 2+ times, remove the repetitions
                if matches >= 2:
                    for rep in range(1, matches + 1):
                        rep_start = start + rep * pattern_length
                        for idx in range(rep_start, rep_start + pattern_length):
                            if idx < len(segment_texts):
                                to_remove.add(idx)
                    
                    pattern_text = " | ".join(p[:30] for p in pattern)
                    logger().debug(f"Detected looping pattern (length {pattern_length}, {matches} repetitions): {pattern_text}...") 

    def _get_optimal_model_for_duration(self, audio_path: str) -> str:
        """Select optimal model based on audio duration and requirements."""
        try:
            duration = librosa.get_duration(path=audio_path)
            return self._config.get_optimal_model(self._model_size, duration)
        except Exception:
            # If we can't determine duration, use requested model
            return self._model_size

    def _get_model_fallback_chain(self, preferred_model: str) -> List[str]:
        """Get fallback model chain for robust transcription."""
        # Define fallback chains for different models
        fallback_chains = {
            "large-v3": ["large-v3", "large-v2", "large", "medium"],
            "large-v2": ["large-v2", "large", "medium"],
            "large": ["large", "large-v2", "medium"],
            "medium": ["medium", "base"],
            "base": ["base", "tiny"],
            "tiny": ["tiny"]
        }
        
        return fallback_chains.get(preferred_model, [preferred_model, "base", "tiny"])

    def _get_model(self, audio_path: str = None):
        if self._model:
            return self._model
        
        import whisper

        # Determine optimal model if audio path provided
        if audio_path:
            optimal_model = self._get_optimal_model_for_duration(audio_path)
        else:
            optimal_model = self._model_size
        
        # Get fallback chain
        fallback_models = self._get_model_fallback_chain(optimal_model)
        
        last_error = None
        for model_name in fallback_models:
            try:
                logger().debug(f"Attempting to load Whisper model: {model_name}")
                self._model = whisper.load_model(model_name)
                
                # Update model size for future reference
                self._model_size = model_name
                
                if model_name != optimal_model:
                    logger().info(f"Using fallback model {model_name} instead of {optimal_model}")
                
                return self._model
                
            except Exception as e:
                last_error = e
                logger().warning(f"Failed to load model {model_name}: {e}")
                continue
        
        # If all models failed
        raise RuntimeError(
            f"Failed to load any Whisper model from chain {fallback_models}. Last error: {last_error}\n" 
            f"Ensure Whisper is installed and models are available (or can be downloaded)."
        )