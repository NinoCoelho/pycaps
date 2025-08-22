"""Translation quality validation for subtitle generation."""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ..common.models import Document, Segment, Word

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Translation quality metrics."""
    total_segments: int = 0
    total_words: int = 0
    
    # Reading speed metrics
    reading_speed_issues: int = 0
    avg_chars_per_second: float = 0.0
    max_chars_per_second: float = 0.0
    
    # Line length metrics
    line_length_issues: int = 0
    avg_line_length: float = 0.0
    max_line_length: int = 0
    
    # Duration metrics
    duration_issues: int = 0
    avg_segment_duration: float = 0.0
    min_segment_duration: float = float('inf')
    max_segment_duration: float = 0.0
    
    # Timing issues
    overlapping_segments: int = 0
    gap_issues: int = 0
    
    # Translation specific
    empty_translations: int = 0
    suspicious_translations: int = 0
    word_count_variance: float = 0.0  # Ratio of target/source words
    
    # Quality score (0.0 to 1.0, where 1.0 is perfect)
    overall_quality_score: float = 0.0


class TranslationQualityValidator:
    """Validates the quality of translated subtitles."""
    
    def __init__(
        self,
        max_reading_speed: int = 20,  # chars per second
        max_line_length: int = 42,
        max_duration: float = 7.0,
        min_duration: float = 0.5,
        max_gap: float = 3.0  # seconds
    ):
        """
        Initialize quality validator with thresholds.
        
        Args:
            max_reading_speed: Maximum reading speed in characters per second
            max_line_length: Maximum characters per line
            max_duration: Maximum segment duration in seconds
            min_duration: Minimum segment duration in seconds
            max_gap: Maximum gap between segments in seconds
        """
        self.max_reading_speed = max_reading_speed
        self.max_line_length = max_line_length
        self.max_duration = max_duration
        self.min_duration = min_duration
        self.max_gap = max_gap
    
    def validate_document(self, document: Document) -> QualityMetrics:
        """
        Validate the quality of a translated document.
        
        Args:
            document: Translated document to validate
            
        Returns:
            QualityMetrics with detailed analysis
        """
        metrics = QualityMetrics()
        segments_list = list(document._segments)
        metrics.total_segments = len(segments_list)
        
        if not segments_list:
            logger.warning("No segments to validate")
            return metrics
        
        # Initialize tracking variables
        segment_durations = []
        chars_per_second_values = []
        line_lengths = []
        word_counts = []
        
        # Analyze each segment
        for i, segment in enumerate(segments_list):
            segment_text = self._extract_segment_text(segment)
            duration = segment.time.end - segment.time.start
            
            segment_durations.append(duration)
            word_count = len(segment_text.split())
            word_counts.append(word_count)
            metrics.total_words += word_count
            
            # Check for empty translations
            if not segment_text.strip():
                metrics.empty_translations += 1
                continue
            
            # Reading speed analysis
            if duration > 0:
                chars_per_second = len(segment_text) / duration
                chars_per_second_values.append(chars_per_second)
                
                if chars_per_second > self.max_reading_speed:
                    metrics.reading_speed_issues += 1
            
            # Line length analysis
            lines = segment_text.split('\n')
            for line in lines:
                line_length = len(line.strip())
                line_lengths.append(line_length)
                
                if line_length > self.max_line_length:
                    metrics.line_length_issues += 1
            
            # Duration analysis
            if duration > self.max_duration or duration < self.min_duration:
                metrics.duration_issues += 1
            
            # Check for suspicious translations
            if self._is_suspicious_translation(segment_text):
                metrics.suspicious_translations += 1
            
            # Check overlaps with next segment
            if i < len(segments_list) - 1:
                next_segment = segments_list[i + 1]
                if segment.time.end > next_segment.time.start:
                    metrics.overlapping_segments += 1
                
                # Check gaps
                gap = next_segment.time.start - segment.time.end
                if gap > self.max_gap:
                    metrics.gap_issues += 1
        
        # Calculate aggregate metrics
        if segment_durations:
            metrics.avg_segment_duration = sum(segment_durations) / len(segment_durations)
            metrics.min_segment_duration = min(segment_durations)
            metrics.max_segment_duration = max(segment_durations)
        
        if chars_per_second_values:
            metrics.avg_chars_per_second = sum(chars_per_second_values) / len(chars_per_second_values)
            metrics.max_chars_per_second = max(chars_per_second_values)
        
        if line_lengths:
            metrics.avg_line_length = sum(line_lengths) / len(line_lengths)
            metrics.max_line_length = max(line_lengths)
        
        # Calculate overall quality score
        metrics.overall_quality_score = self._calculate_quality_score(metrics)
        
        return metrics
    
    def validate_translation_pair(
        self, 
        original_document: Document, 
        translated_document: Document
    ) -> Tuple[QualityMetrics, Dict[str, float]]:
        """
        Validate translation quality by comparing original and translated documents.
        
        Args:
            original_document: Original document before translation
            translated_document: Translated document
            
        Returns:
            Tuple of (metrics, comparison_stats)
        """
        # Validate translated document
        metrics = self.validate_document(translated_document)
        
        # Compare with original
        comparison_stats = self._compare_documents(original_document, translated_document)
        metrics.word_count_variance = comparison_stats.get('word_count_ratio', 1.0)
        
        return metrics, comparison_stats
    
    def _extract_segment_text(self, segment: Segment) -> str:
        """Extract text from segment."""
        texts = []
        for line in segment._lines:
            line_texts = []
            for word in line._words:
                line_texts.append(word.text)
            if line_texts:
                texts.append(" ".join(line_texts))
        return " ".join(texts)
    
    def _is_suspicious_translation(self, text: str) -> bool:
        """Check if translation looks suspicious."""
        text_lower = text.lower().strip()
        
        # Common signs of poor translation
        suspicious_patterns = [
            # Common mistranslations or untranslated phrases
            "thank you for watching",
            "please subscribe", 
            "like and subscribe",
            "subtitles by",
            "[music]",
            "[applause]",
            "[inaudible]",
            # Repeated characters (often transcription errors)
            "aaaa", "eeee", "oooo", "hhhh",
            # Very short repeated words
            "a a a a", "o o o o", "e e e e",
            # URLs or email addresses (shouldn't be translated)
            "http://", "https://", "www.", ".com", ".org", "@"
        ]
        
        for pattern in suspicious_patterns:
            if pattern in text_lower:
                return True
        
        # Check for excessive repetition of single characters
        if len(text) > 10:
            char_counts = {}
            for char in text_lower:
                if char.isalpha():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            for char, count in char_counts.items():
                if count > len(text) * 0.3:  # More than 30% is same character
                    return True
        
        return False
    
    def _compare_documents(
        self, 
        original: Document, 
        translated: Document
    ) -> Dict[str, float]:
        """Compare original and translated documents."""
        original_segments = list(original._segments)
        translated_segments = list(translated._segments)
        
        stats = {
            'segment_count_match': len(original_segments) == len(translated_segments),
            'original_segment_count': len(original_segments),
            'translated_segment_count': len(translated_segments),
            'timing_differences': [],
            'word_count_ratios': [],
            'length_ratios': []
        }
        
        # Compare paired segments
        min_segments = min(len(original_segments), len(translated_segments))
        
        for i in range(min_segments):
            orig_seg = original_segments[i]
            trans_seg = translated_segments[i]
            
            orig_text = self._extract_segment_text(orig_seg)
            trans_text = self._extract_segment_text(trans_seg)
            
            # Timing difference
            timing_diff = abs(orig_seg.time.start - trans_seg.time.start)
            stats['timing_differences'].append(timing_diff)
            
            # Word count ratio
            orig_words = len(orig_text.split()) if orig_text.strip() else 0
            trans_words = len(trans_text.split()) if trans_text.strip() else 0
            
            if orig_words > 0:
                word_ratio = trans_words / orig_words
                stats['word_count_ratios'].append(word_ratio)
            
            # Length ratio
            if len(orig_text) > 0:
                length_ratio = len(trans_text) / len(orig_text)
                stats['length_ratios'].append(length_ratio)
        
        # Calculate averages
        if stats['timing_differences']:
            stats['avg_timing_diff'] = sum(stats['timing_differences']) / len(stats['timing_differences'])
        
        if stats['word_count_ratios']:
            stats['word_count_ratio'] = sum(stats['word_count_ratios']) / len(stats['word_count_ratios'])
        else:
            stats['word_count_ratio'] = 1.0
        
        if stats['length_ratios']:
            stats['avg_length_ratio'] = sum(stats['length_ratios']) / len(stats['length_ratios'])
        
        return stats
    
    def _calculate_quality_score(self, metrics: QualityMetrics) -> float:
        """Calculate overall quality score from 0.0 to 1.0."""
        if metrics.total_segments == 0:
            return 0.0
        
        # Penalty factors (0.0 = perfect, 1.0 = completely broken)
        penalties = []
        
        # Reading speed penalty
        if metrics.total_segments > 0:
            reading_penalty = min(metrics.reading_speed_issues / metrics.total_segments, 1.0)
            penalties.append(reading_penalty * 0.3)  # 30% weight
        
        # Line length penalty
        if metrics.total_segments > 0:
            line_penalty = min(metrics.line_length_issues / metrics.total_segments, 1.0)
            penalties.append(line_penalty * 0.2)  # 20% weight
        
        # Duration penalty
        if metrics.total_segments > 0:
            duration_penalty = min(metrics.duration_issues / metrics.total_segments, 1.0)
            penalties.append(duration_penalty * 0.2)  # 20% weight
        
        # Overlap penalty
        if metrics.total_segments > 0:
            overlap_penalty = min(metrics.overlapping_segments / metrics.total_segments, 1.0)
            penalties.append(overlap_penalty * 0.1)  # 10% weight
        
        # Empty translation penalty
        if metrics.total_segments > 0:
            empty_penalty = min(metrics.empty_translations / metrics.total_segments, 1.0)
            penalties.append(empty_penalty * 0.1)  # 10% weight
        
        # Suspicious translation penalty
        if metrics.total_segments > 0:
            suspicious_penalty = min(metrics.suspicious_translations / metrics.total_segments, 1.0)
            penalties.append(suspicious_penalty * 0.1)  # 10% weight
        
        # Calculate final score
        total_penalty = sum(penalties)
        quality_score = max(0.0, 1.0 - total_penalty)
        
        return quality_score
    
    def generate_quality_report(self, metrics: QualityMetrics) -> str:
        """Generate a human-readable quality report."""
        report_lines = [
            "=== Translation Quality Report ===",
            f"Total Segments: {metrics.total_segments}",
            f"Total Words: {metrics.total_words}",
            f"Overall Quality Score: {metrics.overall_quality_score:.2f}/1.00",
            "",
            "=== Reading Speed Analysis ===",
            f"Average chars/second: {metrics.avg_chars_per_second:.1f}",
            f"Maximum chars/second: {metrics.max_chars_per_second:.1f}",
            f"Segments with reading speed issues: {metrics.reading_speed_issues}",
            "",
            "=== Line Length Analysis ===",
            f"Average line length: {metrics.avg_line_length:.1f}",
            f"Maximum line length: {metrics.max_line_length}",
            f"Lines exceeding length limit: {metrics.line_length_issues}",
            "",
            "=== Duration Analysis ===",
            f"Average segment duration: {metrics.avg_segment_duration:.1f}s",
            f"Min/Max duration: {metrics.min_segment_duration:.1f}s / {metrics.max_segment_duration:.1f}s",
            f"Segments with duration issues: {metrics.duration_issues}",
            "",
            "=== Timing Issues ===",
            f"Overlapping segments: {metrics.overlapping_segments}",
            f"Gap issues: {metrics.gap_issues}",
            "",
            "=== Translation Quality ===",
            f"Empty translations: {metrics.empty_translations}",
            f"Suspicious translations: {metrics.suspicious_translations}",
            f"Word count variance: {metrics.word_count_variance:.2f}",
        ]
        
        # Quality recommendations
        report_lines.extend([
            "",
            "=== Recommendations ==="
        ])
        
        if metrics.overall_quality_score >= 0.9:
            report_lines.append("✅ Excellent quality - no major issues detected")
        elif metrics.overall_quality_score >= 0.8:
            report_lines.append("✅ Good quality - minor improvements possible")
        elif metrics.overall_quality_score >= 0.6:
            report_lines.append("⚠️  Moderate quality - several issues need attention")
        else:
            report_lines.append("❌ Poor quality - significant issues require fixing")
        
        if metrics.reading_speed_issues > 0:
            report_lines.append(f"• Consider splitting {metrics.reading_speed_issues} fast segments")
        
        if metrics.line_length_issues > 0:
            report_lines.append(f"• Shorten {metrics.line_length_issues} long lines")
        
        if metrics.overlapping_segments > 0:
            report_lines.append(f"• Fix {metrics.overlapping_segments} timing overlaps")
        
        if metrics.empty_translations > 0:
            report_lines.append(f"• Address {metrics.empty_translations} empty translations")
        
        if metrics.suspicious_translations > 0:
            report_lines.append(f"• Review {metrics.suspicious_translations} suspicious translations")
        
        return "\n".join(report_lines)