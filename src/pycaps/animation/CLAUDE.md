# Animation Module - Claude Context

**Module Type:** Animation Framework & Engine
**Primary Technologies:** CSS3 Animations, Keyframes, Transforms, Timing Functions
**Dependencies:** Pydantic, typing, math utilities
**Last Updated:** 2025-08-18

## Module Overview

The Animation module provides a sophisticated hierarchical animation system for pycaps subtitles. It combines primitive animation building blocks with preset compositions to create engaging visual effects. The system supports both CSS-based browser animations and frame-by-frame rendering, with intelligent timing and state management.

### Core Architecture
```
Animation Hierarchy:
├── Primitive Animations (atomic building blocks)
│   ├── FadeAnimation
│   ├── SlideAnimation  
│   ├── ScaleAnimation
│   ├── RotateAnimation
│   └── ColorAnimation
└── Preset Animations (composed effects)
    ├── PopInAnimation
    ├── TypewriterAnimation
    ├── BounceAnimation
    └── Custom Compositions
```

### Key Capabilities
- Hierarchical animation composition system
- Element-targeted animations (word, line, segment level)
- State-aware animation sequences
- CSS3 and frame-based rendering support
- Timing function library (easing, bezier curves)
- Animation chaining and synchronization
- Performance-optimized rendering

## Core Design Principles

### 1. Composition Over Inheritance
```python
# Build complex animations from simple primitives
pop_in = CompositeAnimation([
    ScaleAnimation(from_scale=0.0, to_scale=1.0, duration=0.3),
    FadeAnimation(from_opacity=0.0, to_opacity=1.0, duration=0.3),
    RotateAnimation(from_rotation=0, to_rotation=360, duration=0.5)
])
```

### 2. Element Targeting
```python
# Target specific elements in the subtitle hierarchy
word_animation = Animation(target="word", effects=[...])
line_animation = Animation(target="line", effects=[...])
segment_animation = Animation(target="segment", effects=[...])
```

### 3. State Management
```python
# Animations aware of element state
class StateAwareAnimation:
    def get_animation_for_state(self, element: Element, state: str) -> Animation:
        if state == "entering":
            return self.entrance_animation
        elif state == "visible":
            return self.idle_animation
        elif state == "exiting":
            return self.exit_animation
```

## Key Components

### 1. Base Animation System (`base_animation.py`)

**Purpose**: Abstract foundation for all animations
```python
class BaseAnimation(ABC):
    def __init__(
        self,
        duration: float,
        delay: float = 0.0,
        timing_function: str = "ease",
        fill_mode: str = "forwards"
    ):
        self.duration = duration
        self.delay = delay
        self.timing_function = timing_function
        self.fill_mode = fill_mode
    
    @abstractmethod
    def generate_css(self, element: Element) -> str:
        """Generate CSS animation for browser rendering"""
        pass
    
    @abstractmethod
    def get_keyframes(self, element: Element) -> List[Keyframe]:
        """Get keyframes for frame-by-frame rendering"""
        pass
    
    @abstractmethod
    def apply_at_progress(self, element: Element, progress: float) -> Dict[str, Any]:
        """Apply animation at specific progress (0.0-1.0)"""
        pass
```

### 2. Primitive Animations (`primitives/`)

#### Fade Animation (`fade_animation.py`)
```python
class FadeAnimation(BaseAnimation):
    def __init__(
        self,
        from_opacity: float = 0.0,
        to_opacity: float = 1.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.from_opacity = from_opacity
        self.to_opacity = to_opacity
    
    def generate_css(self, element: Element) -> str:
        return f"""
        @keyframes fade-{self.get_id()} {{
            from {{ opacity: {self.from_opacity}; }}
            to {{ opacity: {self.to_opacity}; }}
        }}
        
        .{element.css_class} {{
            animation: fade-{self.get_id()} {self.duration}s {self.timing_function} {self.delay}s {self.fill_mode};
        }}
        """
    
    def apply_at_progress(self, element: Element, progress: float) -> Dict[str, Any]:
        opacity = self.from_opacity + (self.to_opacity - self.from_opacity) * progress
        return {"opacity": opacity}
```

#### Slide Animation (`slide_animation.py`)
```python
class SlideAnimation(BaseAnimation):
    def __init__(
        self,
        direction: str = "up",  # up, down, left, right
        distance: int = 50,     # pixels
        **kwargs
    ):
        super().__init__(**kwargs)
        self.direction = direction
        self.distance = distance
    
    def generate_css(self, element: Element) -> str:
        transform_from = self._get_transform_value(1.0)
        transform_to = self._get_transform_value(0.0)
        
        return f"""
        @keyframes slide-{self.direction}-{self.get_id()} {{
            from {{ transform: {transform_from}; }}
            to {{ transform: {transform_to}; }}
        }}
        
        .{element.css_class} {{
            animation: slide-{self.direction}-{self.get_id()} {self.duration}s {self.timing_function} {self.delay}s {self.fill_mode};
        }}
        """
    
    def _get_transform_value(self, progress: float) -> str:
        offset = self.distance * progress
        if self.direction == "up":
            return f"translateY({offset}px)"
        elif self.direction == "down":
            return f"translateY(-{offset}px)"
        elif self.direction == "left":
            return f"translateX({offset}px)"
        elif self.direction == "right":
            return f"translateX(-{offset}px)"
```

#### Scale Animation (`scale_animation.py`)
```python
class ScaleAnimation(BaseAnimation):
    def __init__(
        self,
        from_scale: float = 0.0,
        to_scale: float = 1.0,
        origin: str = "center",  # center, top-left, etc.
        **kwargs
    ):
        super().__init__(**kwargs)
        self.from_scale = from_scale
        self.to_scale = to_scale
        self.origin = origin
    
    def generate_css(self, element: Element) -> str:
        return f"""
        @keyframes scale-{self.get_id()} {{
            from {{ 
                transform: scale({self.from_scale}); 
                transform-origin: {self.origin};
            }}
            to {{ 
                transform: scale({self.to_scale}); 
                transform-origin: {self.origin};
            }}
        }}
        
        .{element.css_class} {{
            animation: scale-{self.get_id()} {self.duration}s {self.timing_function} {self.delay}s {self.fill_mode};
        }}
        """
```

### 3. Preset Animations (`presets/`)

#### Pop-In Animation (`pop_in_animation.py`)
```python
class PopInAnimation(CompositeAnimation):
    def __init__(self, intensity: float = 1.0, **kwargs):
        # Combine multiple primitives
        animations = [
            ScaleAnimation(
                from_scale=0.0,
                to_scale=1.0 + (0.2 * intensity),
                duration=kwargs.get('duration', 0.4) * 0.6
            ),
            ScaleAnimation(
                from_scale=1.0 + (0.2 * intensity),
                to_scale=1.0,
                duration=kwargs.get('duration', 0.4) * 0.4,
                delay=kwargs.get('duration', 0.4) * 0.6
            ),
            FadeAnimation(
                from_opacity=0.0,
                to_opacity=1.0,
                duration=kwargs.get('duration', 0.4) * 0.3
            )
        ]
        super().__init__(animations, **kwargs)
```

#### Typewriter Animation (`typewriter_animation.py`)
```python
class TypewriterAnimation(BaseAnimation):
    def __init__(self, chars_per_second: float = 10.0, **kwargs):
        self.chars_per_second = chars_per_second
        super().__init__(**kwargs)
    
    def generate_css(self, element: Element) -> str:
        text_length = len(element.text)
        duration = text_length / self.chars_per_second
        
        return f"""
        @keyframes typewriter-{self.get_id()} {{
            from {{ width: 0; }}
            to {{ width: 100%; }}
        }}
        
        .{element.css_class} {{
            width: 0;
            overflow: hidden;
            white-space: nowrap;
            border-right: 2px solid;
            animation: 
                typewriter-{self.get_id()} {duration}s steps({text_length}, end) {self.delay}s {self.fill_mode},
                blink-cursor 1s step-end infinite;
        }}
        
        @keyframes blink-cursor {{
            from, to {{ border-color: transparent; }}
            50% {{ border-color: currentColor; }}
        }}
        """
```

#### Bounce Animation (`bounce_animation.py`)
```python
class BounceAnimation(BaseAnimation):
    def __init__(self, bounce_height: int = 20, bounces: int = 3, **kwargs):
        self.bounce_height = bounce_height
        self.bounces = bounces
        super().__init__(**kwargs)
    
    def generate_css(self, element: Element) -> str:
        keyframes = []
        for i in range(self.bounces + 1):
            progress = i / self.bounces
            height = self.bounce_height * (1 - progress) ** 2
            keyframe_progress = (i / self.bounces) * 100
            keyframes.append(f"{keyframe_progress}% {{ transform: translateY(-{height}px); }}")
        
        keyframes_str = "\n            ".join(keyframes)
        
        return f"""
        @keyframes bounce-{self.get_id()} {{
            {keyframes_str}
        }}
        
        .{element.css_class} {{
            animation: bounce-{self.get_id()} {self.duration}s {self.timing_function} {self.delay}s {self.fill_mode};
        }}
        """
```

### 4. Composite Animation System (`composite_animation.py`)

**Purpose**: Combine multiple animations with synchronization
```python
class CompositeAnimation(BaseAnimation):
    def __init__(self, animations: List[BaseAnimation], **kwargs):
        self.animations = animations
        self.sync_mode = kwargs.pop('sync_mode', 'parallel')  # parallel, sequential
        super().__init__(**kwargs)
    
    def generate_css(self, element: Element) -> str:
        if self.sync_mode == 'parallel':
            return self._generate_parallel_css(element)
        else:
            return self._generate_sequential_css(element)
    
    def _generate_parallel_css(self, element: Element) -> str:
        # All animations run simultaneously
        css_parts = []
        animation_names = []
        
        for i, animation in enumerate(self.animations):
            css_parts.append(animation.generate_css(element))
            animation_names.append(f"{animation.get_name()}-{animation.get_id()}")
        
        # Combine all animations in single declaration
        combined_animation = ", ".join([
            f"{name} {anim.duration}s {anim.timing_function} {anim.delay}s {anim.fill_mode}"
            for name, anim in zip(animation_names, self.animations)
        ])
        
        css_parts.append(f"""
        .{element.css_class} {{
            animation: {combined_animation};
        }}
        """)
        
        return "\n".join(css_parts)
    
    def _generate_sequential_css(self, element: Element) -> str:
        # Animations run one after another
        css_parts = []
        cumulative_delay = self.delay
        
        for animation in self.animations:
            # Clone animation with adjusted delay
            sequential_anim = animation.clone()
            sequential_anim.delay = cumulative_delay
            css_parts.append(sequential_anim.generate_css(element))
            cumulative_delay += animation.duration
        
        return "\n".join(css_parts)
```

### 5. Animation Engine (`animation_engine.py`)

**Purpose**: Central orchestrator for animation management
```python
class AnimationEngine:
    def __init__(self):
        self.registered_animations = {}
        self.animation_sequences = {}
        self._register_built_in_animations()
    
    def register_animation(self, name: str, animation_class: Type[BaseAnimation]):
        """Register custom animation"""
        self.registered_animations[name] = animation_class
    
    def create_animation(self, name: str, **kwargs) -> BaseAnimation:
        """Factory method for creating animations"""
        if name not in self.registered_animations:
            raise ValueError(f"Unknown animation: {name}")
        
        animation_class = self.registered_animations[name]
        return animation_class(**kwargs)
    
    def create_sequence(self, sequence_config: List[Dict]) -> AnimationSequence:
        """Create complex animation sequence from configuration"""
        animations = []
        for config in sequence_config:
            animation = self.create_animation(**config)
            animations.append(animation)
        
        return AnimationSequence(animations)
    
    def apply_to_element(
        self, 
        element: Element, 
        animation: BaseAnimation,
        context: AnimationContext
    ) -> AnimationResult:
        """Apply animation to specific element"""
        if element.type == "word":
            return self._apply_word_animation(element, animation, context)
        elif element.type == "line":
            return self._apply_line_animation(element, animation, context)
        elif element.type == "segment":
            return self._apply_segment_animation(element, animation, context)
```

### 6. Timing Functions (`timing_functions.py`)

**Purpose**: Advanced easing and timing controls
```python
class TimingFunctions:
    # Built-in CSS timing functions
    EASE = "ease"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    LINEAR = "linear"
    
    # Custom cubic-bezier functions
    BOUNCE = "cubic-bezier(0.68, -0.55, 0.265, 1.55)"
    ELASTIC = "cubic-bezier(0.175, 0.885, 0.32, 1.275)"
    BACK = "cubic-bezier(0.6, -0.28, 0.735, 0.045)"
    
    @staticmethod
    def custom_bezier(p1x: float, p1y: float, p2x: float, p2y: float) -> str:
        """Create custom cubic-bezier timing function"""
        return f"cubic-bezier({p1x}, {p1y}, {p2x}, {p2y})"
    
    @staticmethod
    def steps(count: int, direction: str = "end") -> str:
        """Create stepped timing function"""
        return f"steps({count}, {direction})"
```

## Animation Configuration

### JSON Configuration Format
```json
{
  "animations": {
    "entrance": {
      "type": "composite",
      "sync_mode": "parallel",
      "animations": [
        {
          "type": "fade",
          "from_opacity": 0.0,
          "to_opacity": 1.0,
          "duration": 0.5,
          "timing_function": "ease-out"
        },
        {
          "type": "slide",
          "direction": "up",
          "distance": 30,
          "duration": 0.5,
          "timing_function": "ease-out"
        }
      ]
    },
    "emphasis": {
      "type": "scale",
      "from_scale": 1.0,
      "to_scale": 1.2,
      "duration": 0.2,
      "timing_function": "ease-in-out"
    },
    "exit": {
      "type": "fade",
      "from_opacity": 1.0,
      "to_opacity": 0.0,
      "duration": 0.3,
      "timing_function": "ease-in"
    }
  }
}
```

### Programmatic Configuration
```python
# Create animation sequence
entrance_sequence = AnimationSequence([
    FadeAnimation(from_opacity=0, to_opacity=1, duration=0.5),
    SlideAnimation(direction="up", distance=30, duration=0.5),
    ScaleAnimation(from_scale=0.8, to_scale=1.0, duration=0.3, delay=0.2)
])

# Apply to elements
for word in segment.words:
    animation_engine.apply_to_element(word, entrance_sequence, context)
```

## Performance Optimization

### Animation Batching
```python
class AnimationBatcher:
    def __init__(self, max_batch_size: int = 50):
        self.max_batch_size = max_batch_size
        self.batches = []
    
    def add_animation(self, element: Element, animation: BaseAnimation):
        current_batch = self._get_current_batch()
        current_batch.append((element, animation))
        
        if len(current_batch) >= self.max_batch_size:
            self._start_new_batch()
    
    def render_all_batches(self) -> List[AnimationResult]:
        results = []
        for batch in self.batches:
            batch_result = self._render_batch_concurrent(batch)
            results.extend(batch_result)
        return results
```

### CSS Optimization
```python
class CSSOptimizer:
    def optimize_animation_css(self, css: str) -> str:
        # Remove duplicate keyframes
        css = self._deduplicate_keyframes(css)
        
        # Combine similar animations
        css = self._combine_similar_animations(css)
        
        # Minify CSS
        css = self._minify_css(css)
        
        return css
    
    def _deduplicate_keyframes(self, css: str) -> str:
        # Find identical keyframe definitions and merge them
        pass
    
    def _combine_similar_animations(self, css: str) -> str:
        # Combine animations with similar properties
        pass
```

### Memory Management
```python
class AnimationMemoryManager:
    def __init__(self, max_cache_size: int = 1000):
        self.css_cache = {}
        self.keyframe_cache = {}
        self.max_cache_size = max_cache_size
    
    def get_cached_css(self, animation_key: str) -> Optional[str]:
        return self.css_cache.get(animation_key)
    
    def cache_css(self, animation_key: str, css: str):
        if len(self.css_cache) >= self.max_cache_size:
            self._evict_oldest_entries()
        self.css_cache[animation_key] = css
    
    def clear_cache(self):
        self.css_cache.clear()
        self.keyframe_cache.clear()
```

## Integration Points

### Renderer Integration
```python
from ..renderer import CSSRenderer

# Animations generate CSS for renderer
css = animation.generate_css(element)
rendered_image = await renderer.render_with_css(element.text, css)
```

### Template Integration
```python
from ..template import TemplateLoader

# Templates can specify default animations
template = TemplateLoader.load("hype")
default_animations = template.get_animation_config()
```

### Selector Integration
```python
from ..selector import SelectorEngine

# Apply animations to selected elements
selected_words = selector_engine.select_words(criteria)
for word in selected_words:
    animation_engine.apply_animation(word, emphasis_animation)
```

## Development Workflows

### Creating Custom Animations
```python
class CustomGlowAnimation(BaseAnimation):
    def __init__(self, glow_color: str = "#ffff00", intensity: float = 1.0, **kwargs):
        self.glow_color = glow_color
        self.intensity = intensity
        super().__init__(**kwargs)
    
    def generate_css(self, element: Element) -> str:
        glow_size = int(10 * self.intensity)
        return f"""
        @keyframes glow-{self.get_id()} {{
            0% {{ text-shadow: 0 0 5px {self.glow_color}; }}
            50% {{ text-shadow: 0 0 {glow_size}px {self.glow_color}; }}
            100% {{ text-shadow: 0 0 5px {self.glow_color}; }}
        }}
        
        .{element.css_class} {{
            animation: glow-{self.get_id()} {self.duration}s {self.timing_function} {self.delay}s infinite;
        }}
        """

# Register custom animation
animation_engine.register_animation("glow", CustomGlowAnimation)
```

### Testing Animations
```python
import pytest
from pycaps.animation import AnimationEngine, FadeAnimation

def test_fade_animation():
    animation = FadeAnimation(from_opacity=0, to_opacity=1, duration=1.0)
    
    # Test CSS generation
    css = animation.generate_css(mock_element)
    assert "opacity: 0" in css
    assert "opacity: 1" in css
    
    # Test progress application
    result = animation.apply_at_progress(mock_element, 0.5)
    assert result["opacity"] == 0.5
```

### Animation Debugging
```python
class AnimationDebugger:
    def __init__(self, animation_engine: AnimationEngine):
        self.engine = animation_engine
        self.debug_mode = True
    
    def trace_animation(self, animation: BaseAnimation, element: Element):
        if not self.debug_mode:
            return
        
        print(f"Applying {animation.__class__.__name__} to {element}")
        print(f"Duration: {animation.duration}s")
        print(f"Delay: {animation.delay}s")
        print(f"Timing: {animation.timing_function}")
        
        # Generate and save debug CSS
        css = animation.generate_css(element)
        with open(f"debug_animation_{animation.get_id()}.css", "w") as f:
            f.write(css)
```

## Common Use Cases

### Entrance Animations
```python
# Fade in from bottom
entrance = CompositeAnimation([
    FadeAnimation(from_opacity=0, to_opacity=1, duration=0.6),
    SlideAnimation(direction="up", distance=50, duration=0.6)
], sync_mode="parallel")
```

### Emphasis Animations
```python
# Scale and glow for emphasis
emphasis = CompositeAnimation([
    ScaleAnimation(from_scale=1.0, to_scale=1.15, duration=0.2),
    ScaleAnimation(from_scale=1.15, to_scale=1.0, duration=0.2, delay=0.2),
    GlowAnimation(glow_color="#ffff00", duration=0.4)
], sync_mode="parallel")
```

### Exit Animations
```python
# Fade out with scale down
exit = CompositeAnimation([
    FadeAnimation(from_opacity=1, to_opacity=0, duration=0.4),
    ScaleAnimation(from_scale=1.0, to_scale=0.8, duration=0.4)
], sync_mode="parallel")
```

### Typewriter Effect
```python
# Character-by-character reveal
typewriter = TypewriterAnimation(
    chars_per_second=15,
    duration=len(text) / 15,
    timing_function="steps"
)
```

## Troubleshooting Guide

### Common Issues

1. **Animation Not Visible**
   - Check CSS class application
   - Verify animation duration > 0
   - Ensure element has proper styling
   - Check browser CSS support

2. **Performance Issues**
   - Reduce concurrent animations
   - Use CSS transforms instead of layout properties
   - Enable animation batching
   - Optimize timing functions

3. **Timing Synchronization**
   - Use AnimationSequence for complex timing
   - Check delay calculations
   - Verify timing function compatibility

4. **Memory Leaks**
   - Clear animation cache regularly
   - Dispose of animation objects properly
   - Monitor CSS cache size

## API Reference

### Core Classes
- **`BaseAnimation`** - Abstract animation interface
- **`CompositeAnimation`** - Multi-animation coordinator
- **`AnimationEngine`** - Central animation orchestrator
- **`AnimationSequence`** - Sequential animation manager
- **`TimingFunctions`** - Easing and timing utilities

### Primitive Animations
- **`FadeAnimation`** - Opacity transitions
- **`SlideAnimation`** - Position transitions
- **`ScaleAnimation`** - Size transitions
- **`RotateAnimation`** - Rotation effects
- **`ColorAnimation`** - Color transitions

### Preset Animations
- **`PopInAnimation`** - Scale + fade entrance
- **`BounceAnimation`** - Bouncing effects
- **`TypewriterAnimation`** - Character reveal
- **`GlowAnimation`** - Text glow effects

---
*Animation Module | Hierarchical system | CSS3 animations | Composition framework*