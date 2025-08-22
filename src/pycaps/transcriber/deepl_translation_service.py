"""DeepL translation service implementation."""

import os
import time
from typing import List, Optional, Dict, Any
import logging
from .translation_service import TranslationService, TranslationError, TranslationServiceUnavailable

logger = logging.getLogger(__name__)


class DeepLTranslationService(TranslationService):
    """DeepL translation service for high-quality translations."""
    
    def __init__(self, api_key: Optional[str] = None, use_free_api: bool = True):
        """
        Initialize DeepL translation service.
        
        Args:
            api_key: DeepL API key (if None, will try to get from environment)
            use_free_api: Whether to use free API endpoint
        """
        self.api_key = api_key or os.getenv("DEEPL_API_KEY")
        self.use_free_api = use_free_api
        self._translator = None
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
    def _get_translator(self):
        """Lazy load DeepL translator."""
        if self._translator is None:
            try:
                from deep_translator import DeeplTranslator
                
                if not self.api_key:
                    raise TranslationServiceUnavailable(
                        "DeepL API key not found. Set DEEPL_API_KEY environment variable."
                    )
                
                self._translator = DeeplTranslator(
                    api_key=self.api_key,
                    source="en",
                    target="pt",
                    use_free_api=self.use_free_api
                )
                
                logger.info("DeepL translator initialized successfully")
                
            except ImportError:
                raise TranslationServiceUnavailable(
                    "deep-translator library not found. Install with: pip install deep-translator"
                )
            except Exception as e:
                raise TranslationServiceUnavailable(f"Failed to initialize DeepL translator: {e}")
        
        return self._translator
    
    def _rate_limit(self):
        """Apply rate limiting to avoid API limits."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def translate(self, text: str, source_language: str = "en", target_language: str = "pt") -> str:
        """Translate text using DeepL."""
        if not text or not text.strip():
            return text
            
        try:
            self._rate_limit()
            translator = self._get_translator()
            
            # Update source and target languages
            translator.source = source_language
            translator.target = target_language
            
            result = translator.translate(text)
            logger.debug(f"DeepL translation: '{text}' -> '{result}'")
            
            return result
            
        except Exception as e:
            logger.error(f"DeepL translation failed: {e}")
            raise TranslationError(f"DeepL translation failed: {e}")
    
    def translate_batch(
        self, 
        texts: List[str], 
        source_language: str = "en", 
        target_language: str = "pt"
    ) -> List[str]:
        """
        Translate multiple texts in batch with context preservation.
        
        DeepL doesn't have a native batch API, so we'll use intelligent batching
        with separators to maintain context while respecting rate limits.
        """
        if not texts:
            return []
        
        # Filter empty texts and keep track of indices
        non_empty_texts = []
        text_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text.strip())
                text_indices.append(i)
        
        if not non_empty_texts:
            return texts
        
        try:
            # Batch texts with separator for context
            batch_size = 5  # Process in groups of 5 for better context
            results = [""] * len(texts)
            
            for i in range(0, len(non_empty_texts), batch_size):
                batch = non_empty_texts[i:i + batch_size]
                batch_indices = text_indices[i:i + batch_size]
                
                # Join with special separator
                combined_text = " [SEP] ".join(batch)
                
                # Translate combined text
                translated_combined = self.translate(
                    combined_text, 
                    source_language, 
                    target_language
                )
                
                # Split back into individual translations
                translated_parts = translated_combined.split(" [SEP] ")
                
                # Handle case where separator wasn't preserved
                if len(translated_parts) != len(batch):
                    logger.warning("DeepL didn't preserve separators, falling back to individual translation")
                    translated_parts = []
                    for text in batch:
                        translated_parts.append(
                            self.translate(text, source_language, target_language)
                        )
                
                # Assign results back to original positions
                for j, translated in enumerate(translated_parts):
                    if j < len(batch_indices):
                        results[batch_indices[j]] = translated.strip()
            
            # Fill in empty texts that weren't translated
            for i, original_text in enumerate(texts):
                if not original_text or not original_text.strip():
                    results[i] = original_text
            
            logger.info(f"DeepL batch translation completed: {len(texts)} texts")
            return results
            
        except Exception as e:
            logger.error(f"DeepL batch translation failed: {e}")
            # Fallback to individual translation
            logger.info("Falling back to individual translation")
            return [
                self.translate(text, source_language, target_language) 
                for text in texts
            ]
    
    def is_available(self) -> bool:
        """Check if DeepL service is available."""
        try:
            self._get_translator()
            return True
        except TranslationServiceUnavailable:
            return False
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get DeepL supported languages."""
        return {
            "en": "English",
            "pt": "Portuguese",
            "pt-BR": "Portuguese (Brazil)",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "nl": "Dutch",
            "pl": "Polish",
            "ru": "Russian",
            "ja": "Japanese",
            "zh": "Chinese"
        }