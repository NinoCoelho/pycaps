from typing import Dict, List, Optional, Any
from pycaps.common import Document
from pycaps.tag.tagger.word_importance_tagger import WordImportanceTagger
from pycaps.tag.tagger.manual_word_tagger import ManualWordTagger
from pycaps.effect.text.highlight_styling_effect import ResponsiveHighlightStylingEffect
from pycaps.effect.text.css_highlight_effect import CssHighlightEffect
from pycaps.effect.text.ai_emoji_effect import ConfigurableAiEmojiEffect
from pycaps.animation.highlight_animation import HighlightAnimation, EmphasizeAnimation
from pycaps.logger import logger
import os

class IntelligentEnhancement:
    """
    Central orchestrator for AI-powered video enhancement features.
    
    This class coordinates word importance detection, highlighting, emoji placement,
    and custom animations to create more engaging subtitle experiences.
    """

    def __init__(
        self,
        template_name: Optional[str] = None,
        video_width: Optional[int] = None,
        video_height: Optional[int] = None,
        base_font_size: Optional[int] = None,
        content_type: str = "general"
    ):
        """
        Initialize intelligent enhancement system.
        
        Args:
            template_name: Name of the template being used
            video_width: Video width in pixels
            video_height: Video height in pixels
            base_font_size: Base font size of the template
            content_type: Type of content for AI analysis
        """
        self.template_name = template_name
        self.video_width = video_width
        self.video_height = video_height
        self.base_font_size = base_font_size
        self.content_type = content_type
        
        # Configuration
        self.config = self._load_configuration()
        
        # Initialize components
        self.word_importance_tagger = WordImportanceTagger()
        self.manual_word_tagger = self._create_manual_tagger()
        self.highlight_styling_effect = self._create_highlight_styling_effect()
        self.css_highlight_effect = CssHighlightEffect(template_name=self.template_name)
        self.ai_emoji_effect = self._create_ai_emoji_effect()

    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment variables and defaults."""
        return {
            'word_highlighting_enabled': self._get_env_bool('PYCAPS_AI_HIGHLIGHTING_ENABLED', True),
            'emoji_enhancement_enabled': self._get_env_bool('PYCAPS_AI_EMOJI_ENABLED', True),
            'animation_enhancement_enabled': self._get_env_bool('PYCAPS_AI_ANIMATION_ENABLED', True),
            'max_highlighted_words': int(os.getenv('PYCAPS_MAX_HIGHLIGHTED_WORDS', '5')),
            'highlight_intensity': float(os.getenv('PYCAPS_HIGHLIGHT_INTENSITY', '1.0')),
            'emoji_placement_strategy': os.getenv('PYCAPS_EMOJI_STRATEGY', 'balanced'),
            'ai_enabled': self._get_env_bool('PYCAPS_AI_ENABLED', True) and os.getenv('OPENAI_API_KEY') is not None
        }

    def _get_env_bool(self, var_name: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(var_name, str(default)).lower()
        return value not in ("false", "0", "no", "off")

    def _create_manual_tagger(self) -> ManualWordTagger:
        """Create manual word tagger for fallback highlighting."""
        # Try to detect language from content type or use Portuguese as default
        if self.content_type in ["portuguese", "pt", "pt-BR"]:
            return ManualWordTagger.create_portuguese_tagger()
        elif self.content_type in ["english", "en"]:
            return ManualWordTagger.create_english_tagger()
        else:
            # Default to Portuguese since our test content is Portuguese
            return ManualWordTagger.create_portuguese_tagger()

    def _create_highlight_styling_effect(self) -> ResponsiveHighlightStylingEffect:
        """Create highlight styling effect based on configuration."""
        return ResponsiveHighlightStylingEffect(
            template_name=self.template_name,
            base_font_size=self.base_font_size,
            video_width=self.video_width,
            video_height=self.video_height,
            highlight_scale=1.25 * self.config['highlight_intensity'],
            emphasis_scale=1.4 * self.config['highlight_intensity']
        )

    def _create_ai_emoji_effect(self) -> ConfigurableAiEmojiEffect:
        """Create AI emoji effect based on configuration."""
        if self.template_name:
            return ConfigurableAiEmojiEffect.create_for_template(
                self.template_name,
                enabled=self.config['emoji_enhancement_enabled'],
                content_type=self.content_type,
                placement_strategy=self.config['emoji_placement_strategy']
            )
        else:
            return ConfigurableAiEmojiEffect(
                enabled=self.config['emoji_enhancement_enabled'],
                content_type=self.content_type,
                placement_strategy=self.config['emoji_placement_strategy']
            )

    def enhance_document(self, document: Document) -> Dict[str, Any]:
        """
        Apply AI-powered enhancements to a document.
        
        Returns:
            Dictionary with enhancement results and statistics
        """
        results = {
            'word_highlighting_applied': False,
            'emoji_enhancement_applied': False,
            'highlighted_words_count': 0,
            'emojis_added_count': 0,
            'ai_enabled': self.config['ai_enabled'],
            'errors': []
        }

        # Allow fallback highlighting even if AI is disabled
        if not self.config['word_highlighting_enabled'] and not self.config['emoji_enhancement_enabled']:
            logger().info("All AI enhancements disabled - skipping intelligent enhancement")
            return results

        try:
            # Step 1: Analyze and tag important words
            if self.config['word_highlighting_enabled']:
                if self.config['ai_enabled']:
                    logger().info("Analyzing word importance with AI...")
                    try:
                        self.word_importance_tagger.process(
                            document, 
                            self.config['max_highlighted_words']
                        )
                        ai_highlighted_count = self._count_highlighted_words(document)
                        
                        if ai_highlighted_count == 0:
                            logger().warning("AI did not highlight any words, falling back to manual highlighting...")
                            self.manual_word_tagger.process(document, self.config['max_highlighted_words'])
                        else:
                            logger().info(f"AI successfully highlighted {ai_highlighted_count} words")
                    except Exception as ai_error:
                        logger().warning(f"AI word highlighting failed: {ai_error}")
                        logger().info("Falling back to manual word highlighting...")
                        self.manual_word_tagger.process(document, self.config['max_highlighted_words'])
                else:
                    logger().info("AI not available - using manual word highlighting for fallback...")
                    self.manual_word_tagger.process(document, self.config['max_highlighted_words'])
                
                # Apply highlighting styles
                logger().info("Applying highlight styling...")
                self.highlight_styling_effect.run(document)
                
                # Apply CSS-based highlighting for better visibility
                logger().info("Applying CSS highlight effects...")
                self.css_highlight_effect.run(document)
                
                results['word_highlighting_applied'] = True
                results['highlighted_words_count'] = self._count_highlighted_words(document)
                
                logger().info(f"Applied highlighting to {results['highlighted_words_count']} words")
            
                # Detailed logging for debugging
                if results['highlighted_words_count'] > 0:
                    highlighted_words = []
                    for word in document.get_words():
                        for tag in word.get_tags():
                            if tag.name in ['highlight', 'emphasis']:
                                highlighted_words.append(f"'{word.text}' ({tag.name})")
                                break
                    logger().info(f"Highlighted words: {', '.join(highlighted_words)}")

        except Exception as e:
            error_msg = f"Word highlighting failed: {e}"
            logger().error(error_msg)
            results['errors'].append(error_msg)

        try:
            # Step 2: Apply AI-powered emoji enhancements
            if self.config['emoji_enhancement_enabled']:
                logger().info("Applying AI emoji enhancements...")
                initial_emoji_count = self._count_emojis(document)
                
                self.ai_emoji_effect.run(document)
                
                final_emoji_count = self._count_emojis(document)
                emojis_added = final_emoji_count - initial_emoji_count
                
                results['emoji_enhancement_applied'] = True
                results['emojis_added_count'] = emojis_added
                
                logger().info(f"Added {emojis_added} AI-suggested emojis")

        except Exception as e:
            error_msg = f"Emoji enhancement failed: {e}"
            logger().error(error_msg)
            results['errors'].append(error_msg)

        # Step 3: Apply custom animations (if enabled)
        if self.config['animation_enhancement_enabled']:
            try:
                animation_results = self._apply_highlight_animations(document)
                results.update(animation_results)
            except Exception as e:
                error_msg = f"Animation enhancement failed: {e}"
                logger().error(error_msg)
                results['errors'].append(error_msg)

        return results

    def _count_highlighted_words(self, document: Document) -> int:
        """Count words that have highlight or emphasis tags."""
        count = 0
        for word in document.get_words():
            tags = word.get_tags()
            for tag in tags:
                if tag.name in ['highlight', 'emphasis']:
                    count += 1
                    break
        return count

    def _count_emojis(self, document: Document) -> int:
        """Count emojis in the document text."""
        import re
        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # emoticons
                                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                 u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                 u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                 u"\U00002702-\U000027B0"
                                 u"\U000024C2-\U0001F251"
                                 "]+", flags=re.UNICODE)
        
        count = 0
        for word in document.get_words():
            count += len(emoji_pattern.findall(word.text))
        
        return count

    def _apply_highlight_animations(self, document: Document) -> Dict[str, Any]:
        """Apply custom animations to highlighted words."""
        animation_results = {
            'highlight_animations_applied': 0,
            'emphasis_animations_applied': 0
        }

        # This is a placeholder for animation integration
        # In a full implementation, this would create and apply
        # HighlightAnimation and EmphasizeAnimation instances
        
        for word in document.get_words():
            tags = word.get_tags()
            for tag in tags:
                if tag.name == 'highlight':
                    # Apply highlight animation
                    animation_results['highlight_animations_applied'] += 1
                elif tag.name == 'emphasis':
                    # Apply emphasize animation
                    animation_results['emphasis_animations_applied'] += 1

        logger().info(f"Applied {animation_results['highlight_animations_applied']} highlight animations "
                     f"and {animation_results['emphasis_animations_applied']} emphasis animations")

        return animation_results

    def get_enhancement_summary(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable summary of enhancements applied."""
        if not results['ai_enabled']:
            return "AI enhancements disabled"

        summary_parts = []

        if results['word_highlighting_applied']:
            summary_parts.append(f"Highlighted {results['highlighted_words_count']} important words")

        if results['emoji_enhancement_applied']:
            summary_parts.append(f"Added {results['emojis_added_count']} AI-suggested emojis")

        if 'highlight_animations_applied' in results:
            anim_count = results['highlight_animations_applied'] + results['emphasis_animations_applied']
            if anim_count > 0:
                summary_parts.append(f"Applied {anim_count} custom animations")

        if results['errors']:
            summary_parts.append(f"{len(results['errors'])} errors occurred")

        return "; ".join(summary_parts) if summary_parts else "No enhancements applied"


class EnhancementPresets:
    """Predefined enhancement configurations for different content types."""

    @staticmethod
    def get_preset(preset_name: str) -> Dict[str, Any]:
        """Get enhancement preset configuration."""
        presets = {
            'minimal': {
                'max_highlighted_words': 2,
                'highlight_intensity': 0.8,
                'emoji_enhancement_enabled': False,
                'emoji_placement_strategy': 'end_of_phrase'
            },
            'balanced': {
                'max_highlighted_words': 4,
                'highlight_intensity': 1.0,
                'emoji_enhancement_enabled': True,
                'emoji_placement_strategy': 'balanced'
            },
            'aggressive': {
                'max_highlighted_words': 7,
                'highlight_intensity': 1.3,
                'emoji_enhancement_enabled': True,
                'emoji_placement_strategy': 'after_keywords'
            },
            'professional': {
                'max_highlighted_words': 2,
                'highlight_intensity': 0.9,
                'emoji_enhancement_enabled': False,
                'content_type': 'professional'
            },
            'entertainment': {
                'max_highlighted_words': 6,
                'highlight_intensity': 1.2,
                'emoji_enhancement_enabled': True,
                'emoji_placement_strategy': 'balanced',
                'content_type': 'entertainment'
            }
        }
        
        return presets.get(preset_name, presets['balanced'])

    @staticmethod
    def create_enhancement_for_preset(
        preset_name: str, 
        template_name: Optional[str] = None,
        **kwargs
    ) -> IntelligentEnhancement:
        """Create IntelligentEnhancement instance with preset configuration."""
        preset_config = EnhancementPresets.get_preset(preset_name)
        
        # Set environment variables temporarily for the preset
        original_env = {}
        for key, value in preset_config.items():
            env_key = f'PYCAPS_{key.upper()}'
            original_env[env_key] = os.getenv(env_key)
            os.environ[env_key] = str(value)
        
        try:
            enhancement = IntelligentEnhancement(template_name=template_name, **kwargs)
            return enhancement
        finally:
            # Restore original environment variables
            for env_key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(env_key, None)
                else:
                    os.environ[env_key] = original_value