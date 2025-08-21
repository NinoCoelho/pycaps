"""
Configuration for anti-hallucination features in Whisper transcription.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pycaps.logger import logger


@dataclass
class AntiHallucinationConfig:
    """Configuration for anti-hallucination features."""
    
    # VAD Configuration
    enable_vad: bool = True
    vad_provider: str = "silero"  # "silero" or "energy"
    vad_aggressiveness: int = 3  # 0-3, higher = more aggressive
    
    # Chunking Configuration
    chunk_length: int = 30  # seconds
    overlap: int = 2  # seconds
    min_chunk_duration: float = 5.0  # minimum chunk duration
    use_chunking_threshold: float = 90.0  # use chunking for videos longer than this
    
    # Adaptive Thresholds
    adaptive_thresholds: bool = True
    compression_ratio_base: float = 2.4
    logprob_base: float = -1.0
    no_speech_base: float = 0.6
    
    # Model Selection
    auto_model_selection: bool = True
    prefer_large_v2_for_long: bool = True
    fallback_enabled: bool = True
    
    # Post-processing Filters
    enable_repetition_filter: bool = True
    enable_semantic_filter: bool = True
    enable_compression_filter: bool = True
    enable_looping_filter: bool = True
    
    # Filter Thresholds
    semantic_similarity_threshold: float = 0.8
    compression_ratio_threshold: float = 4.0
    max_consecutive_repetitions: int = 2
    
    @classmethod
    def get_duration_based_config(cls, duration: float) -> 'AntiHallucinationConfig':
        """Get configuration optimized for specific audio duration."""
        
        if duration > 300:  # 5+ minutes - very aggressive
            return cls(
                enable_vad=True,
                chunk_length=25,  # Shorter chunks
                overlap=3,  # More overlap
                adaptive_thresholds=True,
                compression_ratio_base=2.1,  # Stricter
                logprob_base=-0.8,  # Stricter
                no_speech_base=0.7,  # Stricter
                prefer_large_v2_for_long=True,
                compression_ratio_threshold=3.5,  # Stricter
                semantic_similarity_threshold=0.75,  # Stricter
                max_consecutive_repetitions=1,  # Very strict
            )
        
        elif duration > 120:  # 2-5 minutes - moderate
            return cls(
                enable_vad=True,
                chunk_length=30,
                overlap=2,
                adaptive_thresholds=True,
                compression_ratio_base=2.2,
                logprob_base=-0.9,
                no_speech_base=0.65,
                prefer_large_v2_for_long=True,
                compression_ratio_threshold=3.8,
                semantic_similarity_threshold=0.8,
                max_consecutive_repetitions=2,
            )
        
        elif duration > 60:  # 1-2 minutes - light
            return cls(
                enable_vad=True,
                chunk_length=45,
                overlap=2,
                adaptive_thresholds=True,
                compression_ratio_base=2.3,
                logprob_base=-0.95,
                no_speech_base=0.62,
                prefer_large_v2_for_long=False,
                compression_ratio_threshold=4.0,
                semantic_similarity_threshold=0.8,
                max_consecutive_repetitions=2,
            )
        
        else:  # < 1 minute - minimal
            return cls(
                enable_vad=False,  # Not needed for short videos
                chunk_length=60,
                overlap=1,
                adaptive_thresholds=False,
                use_chunking_threshold=120.0,  # Higher threshold
                prefer_large_v2_for_long=False,
                enable_semantic_filter=False,  # Less filtering
                max_consecutive_repetitions=3,
            )

    def get_whisper_params(self, duration: float) -> Dict[str, Any]:
        """Get Whisper parameters based on configuration and duration."""
        if self.adaptive_thresholds:
            if duration > 300:
                return {
                    'compression_ratio_threshold': self.compression_ratio_base - 0.3,
                    'logprob_threshold': self.logprob_base + 0.2,
                    'no_speech_threshold': self.no_speech_base + 0.1
                }
            elif duration > 120:
                return {
                    'compression_ratio_threshold': self.compression_ratio_base - 0.2,
                    'logprob_threshold': self.logprob_base + 0.1,
                    'no_speech_threshold': self.no_speech_base + 0.05
                }
            else:
                return {
                    'compression_ratio_threshold': self.compression_ratio_base,
                    'logprob_threshold': self.logprob_base,
                    'no_speech_threshold': self.no_speech_base
                }
        else:
            return {
                'compression_ratio_threshold': self.compression_ratio_base,
                'logprob_threshold': self.logprob_base,
                'no_speech_threshold': self.no_speech_base
            }

    def should_use_chunking(self, duration: float) -> bool:
        """Determine if chunking should be used for given duration."""
        return duration > self.use_chunking_threshold

    def get_optimal_model(self, requested_model: str, duration: float) -> str:
        """Get optimal model for given duration."""
        if not self.auto_model_selection:
            return requested_model
        
        # For very long videos, prefer large-v2 over large-v3
        if duration > 300 and self.prefer_large_v2_for_long:
            if requested_model in ["large-v3", "large"]:
                logger().info(f"Long video ({duration:.1f}s): switching from {requested_model} to large-v2 for better stability")
                return "large-v2"
        
        # For moderate length videos, prefer large-v2 over large-v3
        elif duration > 120 and self.prefer_large_v2_for_long:
            if requested_model == "large-v3":
                logger().info(f"Moderate video ({duration:.1f}s): using large-v2 instead of large-v3")
                return "large-v2"
        
        return requested_model

    def log_configuration(self, duration: float):
        """Log the active configuration for debugging."""
        logger().info(f"Anti-hallucination config for {duration:.1f}s video:")
        logger().info(f"  VAD: {self.enable_vad} ({self.vad_provider})")
        logger().info(f"  Chunking: {self.should_use_chunking(duration)} (chunk_length={self.chunk_length}s, overlap={self.overlap}s)")
        logger().info(f"  Adaptive thresholds: {self.adaptive_thresholds}")
        
        if self.adaptive_thresholds:
            params = self.get_whisper_params(duration)
            logger().info(f"  Whisper params: {params}")
        
        logger().info(f"  Filters: repetition={self.enable_repetition_filter}, semantic={self.enable_semantic_filter}, compression={self.enable_compression_filter}")


# Preset configurations for common scenarios
class PresetConfigs:
    """Preset configurations for different use cases."""
    
    @staticmethod
    def maximum_quality() -> AntiHallucinationConfig:
        """Maximum quality configuration - best for important content."""
        return AntiHallucinationConfig(
            enable_vad=True,
            chunk_length=20,
            overlap=3,
            adaptive_thresholds=True,
            compression_ratio_base=2.0,
            logprob_base=-0.7,
            no_speech_base=0.75,
            auto_model_selection=True,
            prefer_large_v2_for_long=True,
            enable_repetition_filter=True,
            enable_semantic_filter=True,
            enable_compression_filter=True,
            enable_looping_filter=True,
            semantic_similarity_threshold=0.75,
            compression_ratio_threshold=3.0,
            max_consecutive_repetitions=1,
        )
    
    @staticmethod
    def balanced() -> AntiHallucinationConfig:
        """Balanced configuration - good quality with reasonable performance."""
        return AntiHallucinationConfig()  # Default values
    
    @staticmethod
    def fast_processing() -> AntiHallucinationConfig:
        """Fast processing configuration - prioritizes speed over quality."""
        return AntiHallucinationConfig(
            enable_vad=False,
            chunk_length=60,
            overlap=1,
            adaptive_thresholds=False,
            auto_model_selection=False,
            enable_semantic_filter=False,
            enable_looping_filter=False,
            use_chunking_threshold=300.0,  # Only chunk very long videos
        )
    
    @staticmethod
    def podcasts() -> AntiHallucinationConfig:
        """Optimized for podcast/long-form content."""
        return AntiHallucinationConfig(
            enable_vad=True,
            chunk_length=45,
            overlap=3,
            adaptive_thresholds=True,
            compression_ratio_base=2.2,
            logprob_base=-0.8,
            no_speech_base=0.65,
            prefer_large_v2_for_long=True,
            use_chunking_threshold=60.0,  # Chunk even shorter podcasts
            enable_repetition_filter=True,
            max_consecutive_repetitions=1,
        )
    
    @staticmethod
    def short_videos() -> AntiHallucinationConfig:
        """Optimized for short-form content (TikTok, etc.)."""
        return AntiHallucinationConfig(
            enable_vad=False,
            chunk_length=30,
            overlap=1,
            adaptive_thresholds=False,
            auto_model_selection=False,
            use_chunking_threshold=120.0,
            enable_semantic_filter=False,
            enable_looping_filter=False,
        )