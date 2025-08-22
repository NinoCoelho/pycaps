"""Google Translate service implementation."""

import time
from typing import List, Optional, Dict, Any
import logging
from .translation_service import TranslationService, TranslationError, TranslationServiceUnavailable

logger = logging.getLogger(__name__)


class GoogleTranslationService(TranslationService):
    """Google Translate service for translation with fallback support."""
    
    def __init__(self):
        """Initialize Google translation service."""
        self._translator = None
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.05  # 50ms between requests
        
    def _get_translator(self):
        """Lazy load Google translator."""
        if self._translator is None:
            try:
                from deep_translator import GoogleTranslator
                
                self._translator = GoogleTranslator(
                    source='auto',
                    target='pt'
                )
                
                logger.info("Google translator initialized successfully")
                
            except ImportError:
                raise TranslationServiceUnavailable(
                    "deep-translator library not found. Install with: pip install deep-translator"
                )
            except Exception as e:
                raise TranslationServiceUnavailable(f"Failed to initialize Google translator: {e}")
        
        return self._translator
    
    def _rate_limit(self):
        """Apply rate limiting to avoid being blocked."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def translate(self, text: str, source_language: str = "en", target_language: str = "pt") -> str:
        """Translate text using Google Translate."""
        if not text or not text.strip():
            return text
            
        try:
            self._rate_limit()
            translator = self._get_translator()
            
            # Update source and target languages
            translator.source = source_language if source_language != "auto" else "auto"
            
            # Map pt-BR to pt for Google Translator
            mapped_target = "pt" if target_language in ["pt-BR", "pt"] else target_language
            translator.target = mapped_target
            
            result = translator.translate(text)
            logger.debug(f"Google translation: '{text}' ({source_language}->{mapped_target}) -> '{result}'")
            
            return result
            
        except Exception as e:
            logger.error(f"Google translation failed: {e}")
            raise TranslationError(f"Google translation failed: {e}")
    
    def translate_batch(
        self, 
        texts: List[str], 
        source_language: str = "en", 
        target_language: str = "pt"
    ) -> List[str]:
        """
        Translate multiple texts in batch with context preservation.
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
            batch_size = 3  # Smaller batches for Google to avoid issues
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
                    logger.warning(f"Google Translate didn't preserve separators: expected {len(batch)} parts, got {len(translated_parts)}. Falling back to individual translation")
                    translated_parts = []
                    for text in batch:
                        try:
                            individual_translation = self.translate(text, source_language, target_language)
                            translated_parts.append(individual_translation)
                            logger.debug(f"Individual translation: '{text}' -> '{individual_translation}'")
                        except Exception as e:
                            logger.error(f"Individual translation failed for '{text}': {e}")
                            # Keep original text as fallback
                            translated_parts.append(text)
                    
                    # Verify we have the correct number of translations
                    if len(translated_parts) != len(batch):
                        logger.error(f"Translation fallback failed: expected {len(batch)} translations, got {len(translated_parts)}")
                        # Pad with original text if needed
                        while len(translated_parts) < len(batch):
                            translated_parts.append(batch[len(translated_parts)])
                
                # Assign results back to original positions
                for j, translated in enumerate(translated_parts):
                    if j < len(batch_indices):
                        results[batch_indices[j]] = translated.strip()
            
            # Fill in empty texts that weren't translated
            for i, original_text in enumerate(texts):
                if not original_text or not original_text.strip():
                    results[i] = original_text
            
            logger.info(f"Google batch translation completed: {len(texts)} texts")
            return results
            
        except Exception as e:
            logger.error(f"Google batch translation failed: {e}")
            # Fallback to individual translation
            logger.info("Falling back to individual translation")
            return [
                self.translate(text, source_language, target_language) 
                for text in texts
            ]
    
    def is_available(self) -> bool:
        """Check if Google Translate service is available."""
        try:
            self._get_translator()
            return True
        except TranslationServiceUnavailable:
            return False
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get Google Translate supported languages (subset)."""
        return {
            "auto": "Auto-detect",
            "en": "English",
            "pt": "Portuguese",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "nl": "Dutch",
            "pl": "Polish",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "tr": "Turkish"
        }