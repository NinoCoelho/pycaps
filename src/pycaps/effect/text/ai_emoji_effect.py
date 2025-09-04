from .text_effect import TextEffect
from pycaps.common import Document, Word
from pycaps.ai.emoji_controller import EmojiController
from pycaps.logger import logger
from typing import List, Optional, Dict, Any
import os

class AiEmojiEffect(TextEffect):
    """
    AI-powered emoji effect that intelligently adds emojis to text based on content analysis.
    
    This effect uses AI to:
    1. Decide whether emojis should be added to the content
    2. Suggest appropriate emojis for different text segments
    3. Place emojis strategically for maximum engagement
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        content_type: str = "general",
        max_emojis_per_segment: int = 2,
        placement_strategy: str = "end_of_phrase",
        fallback_emojis: Optional[List[str]] = None
    ):
        """
        Initialize AI emoji effect.
        
        Args:
            enabled: Whether AI emoji functionality is enabled (None = auto-detect from env)
            content_type: Type of content (general, educational, professional, entertainment)
            max_emojis_per_segment: Maximum emojis per text segment
            placement_strategy: Where to place emojis ("end_of_phrase", "after_keywords", "balanced")
            fallback_emojis: Emojis to use when AI is not available
        """
        self.enabled = self._determine_enabled_state(enabled)
        self.content_type = content_type
        self.max_emojis_per_segment = max_emojis_per_segment
        self.placement_strategy = placement_strategy
        self.fallback_emojis = fallback_emojis or ["😊", "🤩", "💪", "🔥", "✨", "👏", "💯", "🎯"]
        
        self.emoji_controller = EmojiController() if self.enabled else None

    def _determine_enabled_state(self, enabled: Optional[bool]) -> bool:
        """Determine if AI emoji functionality should be enabled."""
        if enabled is not None:
            return enabled
        
        # Check environment variable
        ai_emoji_enabled = os.getenv("PYCAPS_AI_EMOJI_ENABLED", "true").lower()
        if ai_emoji_enabled in ("false", "0", "no", "off"):
            return False
        
        # Check if general AI is enabled
        ai_enabled = os.getenv("PYCAPS_AI_ENABLED", "true").lower()
        if ai_enabled in ("false", "0", "no", "off"):
            return False
        
        # Check if API key is available
        return os.getenv("OPENAI_API_KEY") is not None

    def run(self, document: Document) -> None:
        """Apply AI-powered emoji effects to the document."""
        if not self.enabled:
            logger().info("AI emoji effect disabled")
            return

        # Extract text segments from document
        text_segments = self._extract_text_segments(document)
        
        if not text_segments:
            logger().warning("No text segments found for emoji analysis")
            return

        # Get full text for context analysis
        full_text = " ".join(text_segments)
        
        # Use AI to decide if emojis should be added
        should_add_emojis = self._should_add_emojis(full_text)
        
        if not should_add_emojis:
            logger().info("AI determined that emojis should not be added to this content")
            return

        # Get AI emoji suggestions
        emoji_suggestions = self._get_emoji_suggestions(text_segments)
        
        # Apply emojis based on suggestions
        self._apply_emoji_suggestions(document, emoji_suggestions)

    def _extract_text_segments(self, document: Document) -> List[str]:
        """Extract text segments from document for analysis."""
        segments = []
        for segment in document.segments:
            segment_text = []
            for line in segment.lines:
                line_words = [word.text for word in line.words]
                segment_text.append(' '.join(line_words))
            
            if segment_text:
                segments.append(' '.join(segment_text))
        
        return segments

    def _should_add_emojis(self, text: str) -> bool:
        """Use AI to determine if emojis should be added."""
        if not self.emoji_controller:
            # Fallback logic
            return self.content_type in ["general", "entertainment", "social", "motivational"]
        
        try:
            return self.emoji_controller.should_add_emojis(text, self.content_type)
        except Exception as e:
            logger().warning(f"AI emoji decision failed: {e}")
            return True  # Default to adding emojis on error

    def _get_emoji_suggestions(self, text_segments: List[str]) -> List[Dict]:
        """Get AI suggestions for emojis in each segment."""
        if not self.emoji_controller:
            return self._get_fallback_suggestions(text_segments)
        
        try:
            return self.emoji_controller.suggest_emojis_for_segments(
                text_segments, 
                self.max_emojis_per_segment
            )
        except Exception as e:
            logger().warning(f"AI emoji suggestions failed: {e}")
            return self._get_fallback_suggestions(text_segments)

    def _get_fallback_suggestions(self, text_segments: List[str]) -> List[Dict]:
        """Generate fallback emoji suggestions when AI is not available."""
        suggestions = []
        
        for i, segment in enumerate(text_segments):
            # Simple keyword-based emoji selection
            suggested_emojis = []
            segment_lower = segment.lower()
            
            # Emotion keywords
            if any(word in segment_lower for word in ["amazing", "awesome", "incredible"]):
                suggested_emojis.append("🤩")
            elif any(word in segment_lower for word in ["love", "heart", "adore"]):
                suggested_emojis.append("❤️")
            elif any(word in segment_lower for word in ["fire", "hot", "blazing"]):
                suggested_emojis.append("🔥")
            elif any(word in segment_lower for word in ["power", "strong", "strength"]):
                suggested_emojis.append("💪")
            elif any(word in segment_lower for word in ["money", "cash", "rich"]):
                suggested_emojis.append("💰")
            elif any(word in segment_lower for word in ["success", "goal", "target"]):
                suggested_emojis.append("🎯")
            elif any(word in segment_lower for word in ["new", "fresh", "novel"]):
                suggested_emojis.append("✨")
            
            # If no keywords matched, randomly select from fallback emojis
            if not suggested_emojis and len(self.fallback_emojis) > 0:
                import random
                suggested_emojis = [random.choice(self.fallback_emojis)]
            
            suggestions.append({
                "segment_index": i,
                "emojis": suggested_emojis[:self.max_emojis_per_segment],
                "reasoning": "keyword-based fallback"
            })
        
        return suggestions

    def _apply_emoji_suggestions(self, document: Document, suggestions: List[Dict]) -> None:
        """Apply emoji suggestions to the document."""
        applied_count = 0
        
        for suggestion in suggestions:
            segment_index = suggestion.get("segment_index", 0)
            emojis = suggestion.get("emojis", [])
            
            if not emojis:
                continue
            
            # Find the corresponding segment in the document
            if segment_index < len(document.segments):
                segment = document.segments[segment_index]
                
                if self.placement_strategy == "end_of_phrase":
                    applied_count += self._apply_emojis_end_of_phrase(segment, emojis)
                elif self.placement_strategy == "after_keywords":
                    applied_count += self._apply_emojis_after_keywords(segment, emojis)
                elif self.placement_strategy == "balanced":
                    applied_count += self._apply_emojis_balanced(segment, emojis)
        
        if applied_count > 0:
            logger().info(f"Applied {applied_count} AI-suggested emojis to the document")

    def _apply_emojis_end_of_phrase(self, segment, emojis: List[str]) -> int:
        """Apply emojis at the end of phrases in the segment."""
        applied = 0
        
        if not segment.lines:
            return applied
        
        # Add emoji to the last word of the segment
        last_line = segment.lines[-1]
        if last_line.words:
            last_word = last_line.words[-1]
            if emojis:
                last_word.text += f" {emojis[0]}"
                applied += 1
        
        return applied

    def _apply_emojis_after_keywords(self, segment, emojis: List[str]) -> int:
        """Apply emojis after important keywords in the segment."""
        applied = 0
        emoji_index = 0
        
        # Keywords that often benefit from emojis
        emoji_keywords = {
            "amazing": "🤩", "awesome": "😎", "incredible": "🤯", "wow": "😮",
            "love": "❤️", "hate": "😠", "excited": "🤩", "happy": "😊",
            "money": "💰", "success": "🎯", "fire": "🔥", "power": "💪"
        }
        
        for line in segment.lines:
            for word in line.words:
                word_lower = word.text.lower()
                
                # Check if word matches emoji keywords
                if word_lower in emoji_keywords and emoji_index < len(emojis):
                    # Use specific emoji for keyword, or fall back to suggested emoji
                    emoji_to_use = emoji_keywords[word_lower]
                    if emoji_to_use not in emojis:
                        emoji_to_use = emojis[emoji_index]
                    
                    word.text += f" {emoji_to_use}"
                    applied += 1
                    emoji_index += 1
                    
                    if emoji_index >= len(emojis):
                        break
            
            if emoji_index >= len(emojis):
                break
        
        return applied

    def _apply_emojis_balanced(self, segment, emojis: List[str]) -> int:
        """Apply emojis in a balanced way throughout the segment."""
        applied = 0
        
        # Combine end of phrase and keyword strategies
        keyword_applied = self._apply_emojis_after_keywords(segment, emojis[:len(emojis)//2])
        remaining_emojis = emojis[len(emojis)//2:]
        
        if remaining_emojis:
            phrase_applied = self._apply_emojis_end_of_phrase(segment, remaining_emojis)
            applied = keyword_applied + phrase_applied
        else:
            applied = keyword_applied
        
        return applied


class ConfigurableAiEmojiEffect(AiEmojiEffect):
    """
    Configurable version of AI emoji effect that can be easily integrated with templates.
    """

    @classmethod
    def create_for_template(cls, template_name: str, **kwargs) -> 'ConfigurableAiEmojiEffect':
        """Create AI emoji effect configured for a specific template."""
        template_configs = {
            'hype': {
                'content_type': 'entertainment',
                'max_emojis_per_segment': 3,
                'placement_strategy': 'balanced',
                'fallback_emojis': ['🔥', '💯', '🤩', '⚡', '🎯', '💪', '🚀', '✨']
            },
            'minimal': {
                'content_type': 'professional',
                'max_emojis_per_segment': 1,
                'placement_strategy': 'end_of_phrase',
                'fallback_emojis': ['✨', '💡', '🎯', '👍']
            },
            'redpill': {
                'content_type': 'motivational',
                'max_emojis_per_segment': 2,
                'placement_strategy': 'after_keywords',
                'fallback_emojis': ['💊', '🔴', '⚡', '💪', '🎯', '🔥']
            },
            'neon': {
                'content_type': 'entertainment',
                'max_emojis_per_segment': 2,
                'placement_strategy': 'balanced',
                'fallback_emojis': ['⚡', '✨', '🌟', '💫', '🔥', '💎']
            }
        }
        
        config = template_configs.get(template_name, {})
        config.update(kwargs)  # Allow overrides
        
        return cls(**config)

    @classmethod
    def create_disabled(cls) -> 'ConfigurableAiEmojiEffect':
        """Create a disabled AI emoji effect."""
        return cls(enabled=False)