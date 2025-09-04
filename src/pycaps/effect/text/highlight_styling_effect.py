from .text_effect import TextEffect
from pycaps.common import Document, Word
from pycaps.tag import TagCondition
from pycaps.logger import logger
from typing import Optional, Dict, Any

class HighlightStylingEffect(TextEffect):
    """
    Text effect that applies visual styling to highlighted words.
    
    This effect modifies the visual properties of words tagged as important
    to make them stand out with bigger size, different colors, and enhanced styling.
    """

    def __init__(
        self,
        highlight_scale: float = 1.4,  # More dramatic scaling
        emphasis_scale: float = 1.6,   # Even more dramatic for emphasis
        highlight_color: Optional[str] = "#ffff00",  # Bright yellow by default
        emphasis_color: Optional[str] = "#ff1744",   # Bright red
        highlight_weight: Optional[str] = "900",      # Much bolder
        emphasis_weight: Optional[str] = "900",
        highlight_shadow: Optional[str] = "0 0 8px rgba(255,255,0,0.6), 0 2px 4px rgba(0,0,0,0.3)",  # Glowing shadow
        emphasis_shadow: Optional[str] = "0 0 12px rgba(255,23,68,0.7), 0 4px 8px rgba(0,0,0,0.4)"    # Strong glow
    ):
        """
        Initialize the highlight styling effect.
        
        Args:
            highlight_scale: Font size multiplier for highlighted words
            emphasis_scale: Font size multiplier for emphasized words
            highlight_color: Color for highlighted words (None = inherit)
            emphasis_color: Color for emphasized words
            highlight_weight: Font weight for highlighted words
            emphasis_weight: Font weight for emphasized words
            highlight_shadow: Text shadow for highlighted words
            emphasis_shadow: Text shadow for emphasized words
        """
        self.highlight_scale = highlight_scale
        self.emphasis_scale = emphasis_scale
        self.highlight_color = highlight_color
        self.emphasis_color = emphasis_color
        self.highlight_weight = highlight_weight
        self.emphasis_weight = emphasis_weight
        self.highlight_shadow = highlight_shadow
        self.emphasis_shadow = emphasis_shadow

    def run(self, document: Document) -> None:
        """Apply highlight styling to tagged words in the document."""
        highlighted_count = 0
        emphasized_count = 0
        
        for word in document.get_words():
            # Check for emphasis tag (highest priority)
            if self._has_tag(word, "emphasis"):
                self._apply_emphasis_styling(word)
                emphasized_count += 1
            # Check for highlight tag
            elif self._has_tag(word, "highlight"):
                self._apply_highlight_styling(word)
                highlighted_count += 1
        
        if highlighted_count > 0 or emphasized_count > 0:
            logger().info(f"Applied styling to {highlighted_count} highlighted and {emphasized_count} emphasized words")

    def _has_tag(self, word: Word, tag_name: str) -> bool:
        """Check if word has a specific tag."""
        for tag in word.get_tags():
            if tag.name == tag_name:
                return True
        return False

    def _apply_highlight_styling(self, word: Word) -> None:
        """Apply highlighting styles to a word."""
        # Store styling information in word metadata
        if not hasattr(word, 'custom_styling'):
            word.custom_styling = {}
        
        word.custom_styling.update({
            'font_size_scale': self.highlight_scale,
            'font_weight': self.highlight_weight,
            'color': self.highlight_color,
            'text_shadow': self.highlight_shadow,
            'is_highlighted': True
        })
        
        logger().debug(f"Applied highlight styling to word: '{word.text}'")

    def _apply_emphasis_styling(self, word: Word) -> None:
        """Apply emphasis styles to a word."""
        # Store styling information in word metadata
        if not hasattr(word, 'custom_styling'):
            word.custom_styling = {}
        
        word.custom_styling.update({
            'font_size_scale': self.emphasis_scale,
            'font_weight': self.emphasis_weight,
            'color': self.emphasis_color,
            'text_shadow': self.emphasis_shadow,
            'is_emphasized': True
        })
        
        logger().debug(f"Applied emphasis styling to word: '{word.text}'")


class ResponsiveHighlightStylingEffect(HighlightStylingEffect):
    """
    Advanced version of highlight styling that adapts to template and video dimensions.
    
    This effect automatically adjusts highlight intensities based on the template's
    base styling and video resolution to maintain visual consistency.
    """

    def __init__(
        self,
        template_name: Optional[str] = None,
        base_font_size: Optional[int] = None,
        video_width: Optional[int] = None,
        video_height: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize responsive highlight styling.
        
        Args:
            template_name: Name of the template being used
            base_font_size: Base font size of the template
            video_width: Video width in pixels
            video_height: Video height in pixels
            **kwargs: Additional styling parameters
        """
        # Adjust scaling based on template and video properties
        adjusted_kwargs = self._adjust_parameters_for_context(
            template_name, base_font_size, video_width, video_height, kwargs
        )
        
        super().__init__(**adjusted_kwargs)
        
        self.template_name = template_name
        self.base_font_size = base_font_size
        self.video_dimensions = (video_width, video_height) if video_width and video_height else None

    def _adjust_parameters_for_context(
        self, 
        template_name: Optional[str], 
        base_font_size: Optional[int],
        video_width: Optional[int],
        video_height: Optional[int],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adjust styling parameters based on context."""
        
        # Template-specific adjustments
        if template_name:
            template_adjustments = self._get_template_adjustments(template_name)
            kwargs.update(template_adjustments)
        
        # Font size-based adjustments
        if base_font_size:
            size_adjustments = self._get_size_adjustments(base_font_size)
            kwargs.update(size_adjustments)
        
        # Video dimension adjustments
        if video_width and video_height:
            dimension_adjustments = self._get_dimension_adjustments(video_width, video_height)
            kwargs.update(dimension_adjustments)
        
        return kwargs

    def _get_template_adjustments(self, template_name: str) -> Dict[str, Any]:
        """Get template-specific adjustments."""
        template_configs = {
            'hype': {
                'highlight_scale': 1.5,
                'emphasis_scale': 1.8,
                'highlight_color': '#ffff00',
                'emphasis_color': '#ff1744',
                'highlight_shadow': '0 0 15px rgba(255,255,0,0.8), 0 3px 6px rgba(0,0,0,0.4)',
                'emphasis_shadow': '0 0 20px rgba(255,23,68,0.9), 0 5px 10px rgba(0,0,0,0.5)'
            },
            'redpill': {
                'highlight_scale': 1.4,
                'emphasis_scale': 1.6,
                'highlight_color': '#ff5722',
                'emphasis_color': '#d32f2f',
                'highlight_shadow': '0 0 12px rgba(255,87,34,0.7), 0 4px 8px rgba(0,0,0,0.5)',
                'emphasis_shadow': '0 0 18px rgba(211,47,47,0.8), 0 6px 12px rgba(0,0,0,0.6)'
            },
            'minimal': {
                'highlight_scale': 1.3,
                'emphasis_scale': 1.5,
                'highlight_color': '#333333',
                'emphasis_color': '#000000',
                'highlight_weight': '700',
                'emphasis_weight': '900',
                'highlight_shadow': '0 2px 4px rgba(0,0,0,0.3)',
                'emphasis_shadow': '0 3px 6px rgba(0,0,0,0.4)'
            },
            'neon': {
                'highlight_scale': 1.4,
                'emphasis_scale': 1.7,
                'highlight_color': '#00ff88',
                'emphasis_color': '#ff0080',
                'highlight_shadow': '0 0 20px #00ff88, 0 0 40px rgba(0,255,136,0.6)',
                'emphasis_shadow': '0 0 25px #ff0080, 0 0 50px rgba(255,0,128,0.7)'
            }
        }
        
        return template_configs.get(template_name, {})

    def _get_size_adjustments(self, base_font_size: int) -> Dict[str, Any]:
        """Adjust scaling based on base font size."""
        if base_font_size <= 24:
            # Smaller fonts need more dramatic scaling
            return {
                'highlight_scale': 1.4,
                'emphasis_scale': 1.6
            }
        elif base_font_size >= 48:
            # Larger fonts need more subtle scaling
            return {
                'highlight_scale': 1.15,
                'emphasis_scale': 1.25
            }
        else:
            # Medium fonts use default scaling
            return {}

    def _get_dimension_adjustments(self, width: int, height: int) -> Dict[str, Any]:
        """Adjust styling based on video dimensions."""
        # Calculate video area to determine if it's mobile/desktop
        area = width * height
        
        if area < 500000:  # Mobile/small videos
            return {
                'highlight_scale': 1.3,
                'emphasis_scale': 1.45
            }
        elif area > 2000000:  # Large/4K videos
            return {
                'highlight_scale': 1.2,
                'emphasis_scale': 1.35
            }
        else:
            return {}

    def run(self, document: Document) -> None:
        """Apply responsive highlight styling."""
        super().run(document)
        
        # Log context information
        if self.template_name:
            logger().info(f"Applied responsive highlighting for template: {self.template_name}")
        if self.video_dimensions:
            logger().info(f"Adjusted for video dimensions: {self.video_dimensions[0]}x{self.video_dimensions[1]}")