"""SRT file parser for pycaps transcriber module."""

import re
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class SRTEntry:
    """Represents a single SRT subtitle entry."""
    index: int
    start_time: float  # in seconds
    end_time: float    # in seconds
    text: str


class SRTLoader:
    """Utility class to parse SRT subtitle files."""
    
    # SRT timestamp pattern: 00:00:01,000 --> 00:00:03,500
    TIMESTAMP_PATTERN = re.compile(
        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
    )
    
    # HTML-like tags that might appear in SRT files
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    
    @classmethod
    def load_srt(cls, srt_path: str) -> List[SRTEntry]:
        """
        Load and parse an SRT file into a list of SRTEntry objects.
        
        Args:
            srt_path: Path to the SRT file
            
        Returns:
            List of SRTEntry objects
            
        Raises:
            FileNotFoundError: If the SRT file doesn't exist
            ValueError: If the SRT file is malformed
        """
        srt_file = Path(srt_path)
        if not srt_file.exists():
            raise FileNotFoundError(f"SRT file not found: {srt_path}")
        
        try:
            with open(srt_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(srt_file, 'r', encoding='latin-1') as f:
                content = f.read()
        
        return cls._parse_srt_content(content)
    
    @classmethod
    def _parse_srt_content(cls, content: str) -> List[SRTEntry]:
        """Parse SRT file content into SRTEntry objects."""
        entries = []
        
        # Split content into blocks (separated by double newlines)
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            if not block.strip():
                continue
                
            try:
                entry = cls._parse_srt_block(block.strip())
                if entry:
                    entries.append(entry)
            except ValueError as e:
                # Log warning but continue processing
                print(f"Warning: Skipping malformed SRT entry: {e}")
                continue
        
        return entries
    
    @classmethod
    def _parse_srt_block(cls, block: str) -> Optional[SRTEntry]:
        """Parse a single SRT block into an SRTEntry."""
        lines = block.split('\n')
        
        if len(lines) < 3:
            raise ValueError(f"SRT block has insufficient lines: {block}")
        
        # Parse index (first line)
        try:
            index = int(lines[0].strip())
        except ValueError:
            raise ValueError(f"Invalid SRT index: {lines[0]}")
        
        # Parse timestamp (second line)
        timestamp_match = cls.TIMESTAMP_PATTERN.match(lines[1].strip())
        if not timestamp_match:
            raise ValueError(f"Invalid SRT timestamp format: {lines[1]}")
        
        start_time = cls._parse_timestamp(*timestamp_match.groups()[:4])
        end_time = cls._parse_timestamp(*timestamp_match.groups()[4:8])
        
        if start_time >= end_time:
            raise ValueError(f"Invalid time range: {start_time} >= {end_time}")
        
        # Parse text (remaining lines)
        text_lines = lines[2:]
        text = '\n'.join(text_lines).strip()
        
        if not text:
            # Skip empty entries
            return None
        
        # Clean text of HTML-like formatting
        text = cls._clean_text(text)
        
        return SRTEntry(
            index=index,
            start_time=start_time,
            end_time=end_time,
            text=text
        )
    
    @classmethod
    def _parse_timestamp(cls, hours: str, minutes: str, seconds: str, milliseconds: str) -> float:
        """Convert SRT timestamp components to float seconds."""
        return (
            int(hours) * 3600 +
            int(minutes) * 60 +
            int(seconds) +
            int(milliseconds) / 1000.0
        )
    
    @classmethod
    def _clean_text(cls, text: str) -> str:
        """
        Clean SRT text by removing HTML-like tags and normalizing whitespace.
        
        Args:
            text: Raw SRT text
            
        Returns:
            Cleaned text
        """
        # Remove HTML-like tags (but preserve content)
        text = cls.HTML_TAG_PATTERN.sub('', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @classmethod
    def validate_srt_file(cls, srt_path: str) -> bool:
        """
        Validate if a file is a properly formatted SRT file.
        
        Args:
            srt_path: Path to the SRT file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            entries = cls.load_srt(srt_path)
            return len(entries) > 0
        except (FileNotFoundError, ValueError):
            return False