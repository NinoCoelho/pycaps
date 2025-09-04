from .animation import Animation
from pycaps.common import WordClip, ElementType
from typing import Optional

class HighlightAnimation(Animation):
    """
    Custom animation for highlighted words that makes them bigger and more prominent.
    
    This animation creates a pulsing/scaling effect that draws attention to important words
    while maintaining readability and visual appeal.
    """
    
    def __init__(
        self, 
        scale_factor: float = 1.3,
        duration: float = 0.6,
        delay: float = 0.0,
        pulse_intensity: float = 0.1,
        glow_color: Optional[str] = None
    ):
        """
        Initialize highlight animation.
        
        Args:
            scale_factor: How much bigger the highlighted word should be (1.0 = no change)
            duration: Duration of the highlight animation in seconds
            delay: Delay before animation starts
            pulse_intensity: Intensity of the pulsing effect (0.0 = no pulse, 0.2 = strong pulse)
            glow_color: Optional glow color for extra emphasis (e.g., "#ffff00")
        """
        super().__init__(duration, delay)
        self.scale_factor = scale_factor
        self.pulse_intensity = pulse_intensity
        self.glow_color = glow_color

    def run(self, clip: WordClip, offset: float, what: ElementType) -> None:
        """
        Apply the highlight animation to a word clip.
        
        The animation consists of:
        1. Scale up the word to make it bigger
        2. Optional pulsing effect for continued attention
        3. Optional glow effect for extra emphasis
        """
        if what != ElementType.WORD:
            return  # This animation only applies to words
        
        # Calculate timing
        start_time = offset + self._delay
        end_time = start_time + self._duration
        
        # Base scale animation - make the word bigger
        scale_keyframes = self._generate_scale_keyframes()
        
        # Add scale transforms to the clip
        for keyframe in scale_keyframes:
            keyframe_time = start_time + (keyframe["progress"] * self._duration)
            clip.add_transform(keyframe_time, "scale", keyframe["scale"])
        
        # Add pulsing effect if specified
        if self.pulse_intensity > 0:
            pulse_keyframes = self._generate_pulse_keyframes()
            for keyframe in pulse_keyframes:
                keyframe_time = start_time + (keyframe["progress"] * self._duration)
                # Combine base scale with pulse
                total_scale = keyframe["scale"] * self.scale_factor
                clip.add_transform(keyframe_time, "scale", total_scale)
        
        # Add glow effect if specified
        if self.glow_color:
            glow_keyframes = self._generate_glow_keyframes()
            for keyframe in glow_keyframes:
                keyframe_time = start_time + (keyframe["progress"] * self._duration)
                clip.add_style(keyframe_time, "text-shadow", keyframe["shadow"])
                clip.add_style(keyframe_time, "color", keyframe.get("color", "inherit"))

    def _generate_scale_keyframes(self):
        """Generate keyframes for the scaling animation."""
        return [
            {"progress": 0.0, "scale": 1.0},                    # Start at normal size
            {"progress": 0.2, "scale": self.scale_factor * 1.1}, # Slightly overshoot
            {"progress": 0.4, "scale": self.scale_factor},        # Settle to target size
            {"progress": 1.0, "scale": self.scale_factor}         # Stay at target size
        ]

    def _generate_pulse_keyframes(self):
        """Generate keyframes for the pulsing effect."""
        if self.pulse_intensity <= 0:
            return []
        
        base_scale = self.scale_factor
        pulse_scale = base_scale + self.pulse_intensity
        
        return [
            {"progress": 0.0, "scale": base_scale},
            {"progress": 0.1, "scale": pulse_scale},
            {"progress": 0.2, "scale": base_scale},
            {"progress": 0.4, "scale": pulse_scale},
            {"progress": 0.5, "scale": base_scale},
            {"progress": 0.7, "scale": pulse_scale},
            {"progress": 0.8, "scale": base_scale},
            {"progress": 1.0, "scale": base_scale}
        ]

    def _generate_glow_keyframes(self):
        """Generate keyframes for the glow effect."""
        if not self.glow_color:
            return []
        
        return [
            {
                "progress": 0.0, 
                "shadow": "0 0 0px rgba(0,0,0,0)",
                "color": "inherit"
            },
            {
                "progress": 0.2, 
                "shadow": f"0 0 8px {self.glow_color}",
                "color": "inherit"
            },
            {
                "progress": 0.6, 
                "shadow": f"0 0 12px {self.glow_color}",
                "color": "inherit"
            },
            {
                "progress": 1.0, 
                "shadow": f"0 0 8px {self.glow_color}",
                "color": "inherit"
            }
        ]


class EmphasizeAnimation(Animation):
    """
    Stronger version of highlight animation for words with very high importance.
    
    This creates a more dramatic effect with stronger scaling, color changes,
    and more pronounced visual effects.
    """
    
    def __init__(
        self, 
        scale_factor: float = 1.5,
        duration: float = 0.8,
        delay: float = 0.0,
        color_change: Optional[str] = "#ff6b6b",
        bounce_effect: bool = True
    ):
        """
        Initialize emphasize animation.
        
        Args:
            scale_factor: How much bigger the word should be
            duration: Animation duration
            delay: Delay before animation
            color_change: Optional color to change the text to
            bounce_effect: Whether to add a bouncing effect
        """
        super().__init__(duration, delay)
        self.scale_factor = scale_factor
        self.color_change = color_change
        self.bounce_effect = bounce_effect

    def run(self, clip: WordClip, offset: float, what: ElementType) -> None:
        """Apply the emphasize animation to a word clip."""
        if what != ElementType.WORD:
            return
        
        start_time = offset + self._delay
        
        # Dramatic scale animation with bounce
        if self.bounce_effect:
            scale_keyframes = self._generate_bounce_scale_keyframes()
        else:
            scale_keyframes = self._generate_smooth_scale_keyframes()
        
        for keyframe in scale_keyframes:
            keyframe_time = start_time + (keyframe["progress"] * self._duration)
            clip.add_transform(keyframe_time, "scale", keyframe["scale"])
        
        # Color change animation
        if self.color_change:
            color_keyframes = self._generate_color_keyframes()
            for keyframe in color_keyframes:
                keyframe_time = start_time + (keyframe["progress"] * self._duration)
                clip.add_style(keyframe_time, "color", keyframe["color"])
        
        # Add strong glow effect
        glow_keyframes = self._generate_strong_glow_keyframes()
        for keyframe in glow_keyframes:
            keyframe_time = start_time + (keyframe["progress"] * self._duration)
            clip.add_style(keyframe_time, "text-shadow", keyframe["shadow"])

    def _generate_bounce_scale_keyframes(self):
        """Generate bouncing scale keyframes for dramatic effect."""
        return [
            {"progress": 0.0, "scale": 1.0},
            {"progress": 0.15, "scale": self.scale_factor * 1.2},  # Overshoot
            {"progress": 0.3, "scale": self.scale_factor * 0.9},   # Bounce back
            {"progress": 0.45, "scale": self.scale_factor * 1.05}, # Small bounce
            {"progress": 0.6, "scale": self.scale_factor},         # Settle
            {"progress": 1.0, "scale": self.scale_factor}
        ]

    def _generate_smooth_scale_keyframes(self):
        """Generate smooth scale keyframes."""
        return [
            {"progress": 0.0, "scale": 1.0},
            {"progress": 0.4, "scale": self.scale_factor},
            {"progress": 1.0, "scale": self.scale_factor}
        ]

    def _generate_color_keyframes(self):
        """Generate color change keyframes."""
        return [
            {"progress": 0.0, "color": "inherit"},
            {"progress": 0.3, "color": self.color_change},
            {"progress": 1.0, "color": self.color_change}
        ]

    def _generate_strong_glow_keyframes(self):
        """Generate strong glow effect keyframes."""
        glow_color = self.color_change or "#ffff00"
        return [
            {"progress": 0.0, "shadow": "0 0 0px rgba(0,0,0,0)"},
            {"progress": 0.2, "shadow": f"0 0 15px {glow_color}"},
            {"progress": 0.5, "shadow": f"0 0 20px {glow_color}, 0 0 30px {glow_color}"},
            {"progress": 1.0, "shadow": f"0 0 12px {glow_color}"}
        ]