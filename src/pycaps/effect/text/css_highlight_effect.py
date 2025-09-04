from .text_effect import TextEffect
from pycaps.common import Document, Word
from pycaps.logger import logger
from typing import Optional

class CssHighlightEffect(TextEffect):
    """
    CSS-based highlighting effect that applies CSS classes to highlighted words.
    This integrates properly with the rendering system by adding CSS styles.
    """

    def __init__(
        self,
        template_name: Optional[str] = None,
        renderer = None  # CSS renderer to add styles to
    ):
        """
        Initialize CSS highlight effect.
        
        Args:
            template_name: Name of template for theme-specific styling
            renderer: CSS renderer to add highlight styles to
        """
        self.template_name = template_name
        self.renderer = renderer
        self.css_injected = False

    def run(self, document: Document) -> None:
        """Apply CSS-based highlighting to tagged words."""
        
        # CSS injection now happens in pipeline.prepare() before renderer opens
        # This ensures our CSS overrides template styles
        if not self.css_injected:
            logger().debug("CSS should have been pre-injected in pipeline prepare phase")
            self.css_injected = True
        
        highlighted_count = 0
        emphasized_count = 0
        
        # Add CSS classes to highlighted words based on their tags
        for word in document.get_words():
            word_tags = word.get_tags()
            
            for tag in word_tags:
                if tag.name == "highlight":
                    # The renderer automatically uses tag names as CSS classes
                    # So "highlight" tag becomes CSS class "highlight"
                    highlighted_count += 1
                    logger().debug(f"Applied highlight CSS class to word: '{word.text}'")
                    
                elif tag.name == "emphasis":
                    # The renderer automatically uses tag names as CSS classes
                    # So "emphasis" tag becomes CSS class "emphasis"
                    emphasized_count += 1
                    logger().debug(f"Applied emphasis CSS class to word: '{word.text}'")
        
        if highlighted_count > 0 or emphasized_count > 0:
            logger().info(f"Applied CSS classes: {highlighted_count} highlighted, {emphasized_count} emphasized words")


    def _inject_highlight_css(self):
        """Inject CSS styles for highlighting into the renderer."""
        
        highlight_css = self._generate_highlight_css()
        
        if hasattr(self.renderer, 'append_css'):
            self.renderer.append_css(highlight_css)
            logger().info("Injected highlight CSS styles into renderer")
        elif hasattr(self.renderer, 'add_css'):
            self.renderer.add_css(highlight_css)
            logger().info("Added highlight CSS styles to renderer")
        else:
            logger().warning("Could not inject CSS - renderer does not support CSS addition")

    def _generate_highlight_css(self) -> str:
        """Generate CSS for word highlighting based on template."""
        
        # Get template-specific configurations
        config = self._get_template_highlight_config()
        
        css = f"""
/* Pycaps AI Word Highlighting Styles */
/* Use very specific selectors to override template styles */
.word.highlight.word-being-narrated,
.word.highlight.word-not-narrated-yet,
.word.highlight.word-already-narrated,
.highlight {{
    font-size: {config['highlight_scale'] * 100}% !important;
    font-weight: {config['highlight_weight']} !important;
    color: {config['highlight_color']} !important;
    text-shadow: {config['highlight_shadow']} !important;
    position: relative;
    z-index: 10 !important;
    display: inline-block;
    animation: highlight-pulse 2s ease-in-out !important;
    transform: scale(1.1) !important;
}}

.word.emphasis.word-being-narrated,
.word.emphasis.word-not-narrated-yet,
.word.emphasis.word-already-narrated,
.emphasis {{
    font-size: {config['emphasis_scale'] * 100}% !important;
    font-weight: {config['emphasis_weight']} !important;
    color: {config['emphasis_color']} !important;
    text-shadow: {config['emphasis_shadow']} !important;
    position: relative;
    z-index: 15 !important;
    display: inline-block;
    animation: emphasis-glow 1.5s ease-in-out infinite alternate !important;
    transform: scale(1.05) !important;
}}

/* Highlight pulse animation */
@keyframes highlight-pulse {{
    0% {{ transform: scale(1); }}
    50% {{ transform: scale(1.05); }}
    100% {{ transform: scale(1); }}
}}

/* Emphasis glow animation */
@keyframes emphasis-glow {{
    0% {{ 
        transform: scale(1);
        filter: brightness(1);
    }}
    100% {{ 
        transform: scale(1.02);
        filter: brightness(1.2);
    }}
}}

/* Ensure highlighted words don't break layout */
.word.highlight.word-being-narrated,
.word.highlight.word-not-narrated-yet,
.word.highlight.word-already-narrated,
.highlight,
.word.emphasis.word-being-narrated,
.word.emphasis.word-not-narrated-yet,
.word.emphasis.word-already-narrated,
.emphasis {{
    white-space: nowrap !important;
    vertical-align: baseline !important;
}}
"""
        
        return css

    def _get_template_highlight_config(self) -> dict:
        """Get highlighting configuration based on template."""
        
        configs = {
            'hype': {
                'highlight_scale': 4.0,  # EXTREMELY large  
                'emphasis_scale': 3.5,   # EXTREMELY large
                'highlight_color': '#FF0000',  # Pure bright red
                'emphasis_color': '#00FF00',   # Pure bright green  
                'highlight_weight': '900',
                'emphasis_weight': '900',
                'highlight_shadow': '0 0 50px #FF0000, 0 0 30px #FF0000, 0 0 20px #FF0000',  # MASSIVE red glow
                'emphasis_shadow': '0 0 50px #00FF00, 0 0 30px #00FF00, 0 0 20px #00FF00'    # MASSIVE green glow
            },
            'redpill': {
                'highlight_scale': 1.5,
                'emphasis_scale': 1.7,
                'highlight_color': '#ff5722',
                'emphasis_color': '#d32f2f',
                'highlight_weight': '900',
                'emphasis_weight': '900',
                'highlight_shadow': '0 0 12px rgba(255,87,34,0.7), 0 4px 8px rgba(0,0,0,0.5)',
                'emphasis_shadow': '0 0 18px rgba(211,47,47,0.8), 0 6px 12px rgba(0,0,0,0.6)'
            },
            'default': {
                'highlight_scale': 1.5,
                'emphasis_scale': 1.8,
                'highlight_color': '#ffff00',
                'emphasis_color': '#ff1744',
                'highlight_weight': '900',
                'emphasis_weight': '900',
                'highlight_shadow': '0 0 10px rgba(255,255,0,0.6), 0 2px 4px rgba(0,0,0,0.3)',
                'emphasis_shadow': '0 0 15px rgba(255,23,68,0.7), 0 4px 8px rgba(0,0,0,0.4)'
            }
        }
        
        return configs.get(self.template_name, configs['default'])