"""Abstract base class for translation services."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TranslationService(ABC):
    """Abstract base class for translation services."""
    
    @abstractmethod
    def translate(self, text: str, source_language: str = "en", target_language: str = "pt") -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_language: Source language code (e.g., "en")
            target_language: Target language code (e.g., "pt", "pt-BR")
            
        Returns:
            Translated text
        """
        pass
    
    @abstractmethod
    def translate_batch(
        self, 
        texts: List[str], 
        source_language: str = "en", 
        target_language: str = "pt"
    ) -> List[str]:
        """
        Translate multiple texts in batch for better context preservation.
        
        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            List of translated texts
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the translation service is available and configured."""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported language codes and names."""
        pass


class TranslationError(Exception):
    """Exception raised when translation fails."""
    pass


class TranslationServiceUnavailable(TranslationError):
    """Exception raised when translation service is unavailable."""
    pass