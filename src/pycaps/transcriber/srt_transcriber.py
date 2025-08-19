"""SRT transcriber for pycaps - converts SRT files to pycaps Document structure."""

import re
from typing import List
from pycaps.common import Document, Segment, Line, Word, TimeFragment
from .base_transcriber import AudioTranscriber
from .srt_loader import SRTLoader, SRTEntry


class SRTTranscriber(AudioTranscriber):
    """
    Transcriber that converts SRT subtitle files to pycaps Document format.
    
    This transcriber handles the conversion from SRT format (segment-level timing)
    to pycaps' hierarchical Document structure with word-level timing estimation.
    """
    
    def __init__(self, srt_path: str):
        """
        Initialize SRT transcriber.
        
        Args:
            srt_path: Path to the SRT file to process
        """
        self.srt_path = srt_path
        
    def transcribe(self, audio_path: str) -> Document:
        """
        Convert SRT file to pycaps Document structure.
        
        Note: audio_path parameter is ignored for SRT transcriber as we work
        directly with the subtitle file.
        
        Args:
            audio_path: Ignored for SRT transcriber
            
        Returns:
            Document object with hierarchical subtitle structure
        """
        # Load SRT entries
        srt_entries = SRTLoader.load_srt(self.srt_path)
        
        if not srt_entries:
            raise ValueError(f"No valid SRT entries found in file: {self.srt_path}")
        
        # Convert to Document structure
        document = Document()
        
        for srt_entry in srt_entries:
            segment = self._create_segment_from_srt_entry(srt_entry)
            document.segments.add(segment)
        
        return document
    
    def _create_segment_from_srt_entry(self, srt_entry: SRTEntry) -> Segment:
        """
        Create a pycaps Segment from an SRT entry.
        
        Args:
            srt_entry: SRT entry to convert
            
        Returns:
            Segment object with proper timing and word structure
        """
        segment = Segment()
        segment.time = TimeFragment(start=srt_entry.start_time, end=srt_entry.end_time)
        
        # Split text into lines (SRT can have multiple lines per entry)
        text_lines = srt_entry.text.split('\n')
        
        # Estimate timing for each line
        total_duration = srt_entry.end_time - srt_entry.start_time
        line_count = len(text_lines)
        
        current_time = srt_entry.start_time
        for i, line_text in enumerate(text_lines):
            if not line_text.strip():
                continue
                
            # Estimate line duration based on text length
            line_duration = self._estimate_line_duration(
                line_text, total_duration, i, line_count, text_lines
            )
            
            line = self._create_line_from_text(
                line_text, current_time, current_time + line_duration
            )
            segment.lines.add(line)
            
            current_time += line_duration
        
        return segment
    
    def _estimate_line_duration(self, line_text: str, total_duration: float, 
                              line_index: int, total_lines: int, all_lines: List[str]) -> float:
        """
        Estimate the duration for a single line within a segment.
        
        Args:
            line_text: Text of the current line
            total_duration: Total duration of the segment
            line_index: Index of current line
            total_lines: Total number of lines
            all_lines: All line texts for context
            
        Returns:
            Estimated duration for this line in seconds
        """
        if total_lines == 1:
            return total_duration
        
        # Calculate relative weight based on text characteristics
        line_weights = []
        for text in all_lines:
            if not text.strip():
                line_weights.append(0.1)  # Minimal weight for empty lines
            else:
                # Weight based on character count and word count
                char_weight = len(text.strip())
                word_weight = len(text.strip().split()) * 2  # Words get more weight
                line_weights.append(char_weight + word_weight)
        
        total_weight = sum(line_weights)
        if total_weight == 0:
            return total_duration / total_lines
        
        # Return proportional duration
        return (line_weights[line_index] / total_weight) * total_duration
    
    def _create_line_from_text(self, text: str, start_time: float, end_time: float) -> Line:
        """
        Create a pycaps Line from text with estimated word timings.
        
        Args:
            text: Line text
            start_time: Line start time in seconds
            end_time: Line end time in seconds
            
        Returns:
            Line object with word-level timing
        """
        line = Line()
        line.time = TimeFragment(start=start_time, end=end_time)
        
        # Split into words and estimate individual timings
        words = self._split_into_words(text)
        word_timings = self._estimate_word_timings(words, start_time, end_time)
        
        for word_text, word_start, word_end in word_timings:
            word = Word()
            word.text = word_text
            word.time = TimeFragment(start=word_start, end=word_end)
            line.words.add(word)
        
        return line
    
    def _split_into_words(self, text: str) -> List[str]:
        """
        Split text into words, handling punctuation appropriately.
        
        Args:
            text: Text to split
            
        Returns:
            List of word strings
        """
        # Split on whitespace but preserve punctuation with words
        words = []
        
        # Use regex to split while keeping punctuation attached to words
        word_pattern = re.compile(r'\S+')
        matches = word_pattern.findall(text)
        
        for match in matches:
            # Clean up the word but preserve meaningful punctuation
            word = match.strip()
            if word:
                words.append(word)
        
        return words
    
    def _estimate_word_timings(self, words: List[str], start_time: float, 
                             end_time: float) -> List[tuple]:
        """
        Estimate individual word timings within a line.
        
        Args:
            words: List of words
            start_time: Line start time
            end_time: Line end time
            
        Returns:
            List of tuples (word_text, word_start, word_end)
        """
        if not words:
            return []
        
        if len(words) == 1:
            return [(words[0], start_time, end_time)]
        
        total_duration = end_time - start_time
        
        # Calculate word weights based on characteristics
        word_weights = []
        for word in words:
            weight = self._calculate_word_weight(word)
            word_weights.append(weight)
        
        total_weight = sum(word_weights)
        
        # Distribute time proportionally
        timings = []
        current_time = start_time
        
        for i, (word, weight) in enumerate(zip(words, word_weights)):
            if i == len(words) - 1:
                # Last word gets remaining time
                word_end = end_time
            else:
                word_duration = (weight / total_weight) * total_duration
                word_end = current_time + word_duration
            
            timings.append((word, current_time, word_end))
            current_time = word_end
        
        return timings
    
    def _calculate_word_weight(self, word: str) -> float:
        """
        Calculate relative weight for word timing estimation.
        
        Args:
            word: Word to analyze
            
        Returns:
            Weight factor (higher = longer duration)
        """
        base_weight = 1.0
        
        # Length factor (longer words take more time)
        length_factor = len(word) * 0.1
        
        # Syllable estimation (very rough)
        vowel_count = sum(1 for char in word.lower() if char in 'aeiouy')
        syllable_factor = max(1, vowel_count) * 0.2
        
        # Punctuation factor (words with punctuation might have slight pauses)
        punctuation_factor = 0.1 if re.search(r'[.!?,:;]', word) else 0
        
        # Complexity factor (words with numbers, special chars)
        complexity_factor = 0.1 * sum(1 for char in word if not char.isalpha())
        
        return base_weight + length_factor + syllable_factor + punctuation_factor + complexity_factor