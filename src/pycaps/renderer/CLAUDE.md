# Renderer Module - Claude Context

**Module Type:** CSS Rendering Engine
**Primary Technologies:** Playwright, CSS3, HTML5, Browser Automation, Image Processing
**Dependencies:** PIL/Pillow, asyncio, aiofiles
**Last Updated:** 2025-08-18

## Module Overview

The Renderer module is pycaps' sophisticated CSS rendering engine that transforms styled text into high-quality images. It leverages browser-based rendering through Playwright to achieve pixel-perfect typography, advanced CSS effects, and complex animations. The module provides both synchronous and asynchronous rendering capabilities with comprehensive caching and optimization features.

### Core Capabilities
- Browser-quality CSS rendering with full CSS3 support
- Word-level and line-level image generation
- Advanced typography including web fonts and custom styling
- Multi-layer composition with transparency support
- Intelligent caching system for performance optimization
- Async/await support for concurrent rendering

## Architecture & Design

### Rendering Pipeline
```
Text + CSS → HTML Document → Browser Rendering → Image Capture → Post-Processing → Cached Output
```

### Core Components
1. **CSSRenderer** - Main rendering orchestrator
2. **HTML Generation** - Dynamic HTML document creation
3. **Browser Automation** - Playwright browser control
4. **Image Processing** - PIL-based post-processing
5. **Caching System** - Intelligent result caching
6. **Resource Management** - Browser lifecycle management

## Key Classes & Components

### 1. CSSRenderer (`css_renderer.py`)

**Purpose**: Main rendering interface and orchestrator
**Key Features**:
- Browser instance management
- HTML template generation
- Image capture and processing
- Caching integration
- Error handling and recovery

**Core Methods**:
```python
class CSSRenderer:
    async def render_word(self, word: Word, style: CSSStyle) -> Image
    async def render_line(self, line: Line, style: CSSStyle) -> Image
    async def render_batch(self, items: List[RenderItem]) -> List[Image]
    async def close(self) -> None
```

### 2. HTML Template System

**Purpose**: Generate dynamic HTML for browser rendering
**Template Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        /* CSS styles injected here */
        .word { /* word-specific styling */ }
        .line { /* line-specific styling */ }
        /* Custom animations and effects */
    </style>
</head>
<body>
    <div class="container">
        <span class="word">rendered_text</span>
    </div>
</body>
</html>
```

**Dynamic Content Generation**:
- CSS style injection
- Font loading and management
- Responsive sizing calculations
- Animation timing setup
- Custom property bindings

### 3. Browser Management (`browser_manager.py`)

**Purpose**: Playwright browser lifecycle management
**Features**:
- Browser instance pooling
- Page context management
- Resource cleanup
- Error recovery
- Performance monitoring

**Browser Configuration**:
```python
browser_config = {
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--font-render-hinting=none"
    ]
}
```

### 4. Image Processing Pipeline

**Purpose**: Post-process rendered browser images
**Processing Steps**:
1. **Raw Capture** - Screenshot from browser
2. **Cropping** - Remove unnecessary whitespace
3. **Alpha Channel** - Add transparency support
4. **Quality Enhancement** - Anti-aliasing and sharpening
5. **Format Conversion** - Convert to target format
6. **Metadata Addition** - Add timing and positioning data

**Image Operations**:
```python
def process_rendered_image(raw_image: bytes) -> ProcessedImage:
    # Convert to PIL Image
    image = Image.open(BytesIO(raw_image))
    
    # Auto-crop whitespace
    bbox = image.getbbox()
    cropped = image.crop(bbox)
    
    # Ensure RGBA mode for transparency
    rgba_image = cropped.convert("RGBA")
    
    # Apply post-processing
    enhanced = enhance_quality(rgba_image)
    
    return ProcessedImage(enhanced, metadata)
```

## CSS Integration

### Supported CSS Features
- **Typography**: font-family, font-size, font-weight, text-decoration
- **Colors**: color, background-color, gradients, rgba/hsla
- **Layout**: padding, margin, border, box-shadow
- **Effects**: text-shadow, opacity, transforms
- **Animations**: CSS transitions and keyframe animations
- **Advanced**: backdrop-filter, clip-path, custom properties

### Style Application
```python
css_style = {
    "font-family": "'Inter', 'Helvetica Neue', sans-serif",
    "font-size": "48px",
    "font-weight": "bold",
    "color": "#ffffff",
    "text-shadow": "2px 2px 4px rgba(0,0,0,0.8)",
    "background": "linear-gradient(45deg, #ff6b6b, #4ecdc4)",
    "padding": "20px 30px",
    "border-radius": "15px"
}
```

### Font Management
```python
# Web font loading
@font-face {
    font-family: 'CustomFont';
    src: url('data:font/woff2;base64,...') format('woff2');
}

# Font fallback chains
font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
```

## Caching System

### Cache Architecture
```
Cache Key = hash(text + css_style + font_config + render_settings)
Cache Value = {image_data, metadata, timestamp, access_count}
```

### Cache Types
1. **Memory Cache** - Fast access for recent renders
2. **Disk Cache** - Persistent storage for reuse
3. **Distributed Cache** - Shared cache for multiple instances

### Cache Management
```python
class RenderCache:
    def get(self, cache_key: str) -> Optional[CachedImage]
    def set(self, cache_key: str, image: Image, ttl: int = 3600)
    def invalidate(self, pattern: str)
    def cleanup(self, max_age: int = 86400)
```

### Cache Strategies
- **LRU Eviction** - Remove least recently used items
- **Size Limits** - Automatic cleanup when cache size exceeds limits
- **TTL Management** - Time-based expiration
- **Intelligent Prefetching** - Predict and pre-render likely requests

## Performance Optimization

### Concurrent Rendering
```python
async def render_batch_concurrent(items: List[RenderItem]) -> List[Image]:
    tasks = []
    for item in items:
        task = asyncio.create_task(render_single_item(item))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### Resource Pool Management
```python
class BrowserPool:
    def __init__(self, max_browsers: int = 4):
        self.pool = asyncio.Queue(maxsize=max_browsers)
        self.active_browsers = set()
    
    async def acquire(self) -> Browser:
        return await self.pool.get()
    
    async def release(self, browser: Browser):
        await self.pool.put(browser)
```

### Memory Management
- **Page Recycling** - Reuse browser pages for multiple renders
- **Resource Cleanup** - Automatic cleanup of temporary files
- **Memory Monitoring** - Track and limit memory usage
- **Garbage Collection** - Explicit cleanup of heavy objects

## Animation Rendering

### CSS Animation Support
```css
@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1.0); }
}

.word {
    animation: fadeIn 0.5s ease-out;
}
```

### Frame-by-Frame Rendering
```python
async def render_animation_frames(
    text: str, 
    animation: Animation, 
    duration_ms: int
) -> List[Image]:
    frames = []
    frame_count = duration_ms // 16  # 60fps
    
    for frame in range(frame_count):
        progress = frame / frame_count
        css = animation.get_css_at_progress(progress)
        image = await render_with_css(text, css)
        frames.append(image)
    
    return frames
```

### Animation Optimization
- **Keyframe Sampling** - Render only essential frames
- **Interpolation** - Generate intermediate frames algorithmically
- **Timeline Caching** - Cache animation sequences
- **Batch Rendering** - Render multiple animations concurrently

## Error Handling & Recovery

### Common Error Scenarios
1. **Browser Crashes** - Browser instance becomes unresponsive
2. **Font Loading Failures** - Custom fonts fail to load
3. **CSS Parsing Errors** - Invalid CSS syntax
4. **Memory Exhaustion** - Out of memory during rendering
5. **Timeout Errors** - Rendering takes too long

### Recovery Strategies
```python
async def render_with_fallback(item: RenderItem) -> Image:
    try:
        return await render_primary(item)
    except BrowserCrashError:
        await restart_browser()
        return await render_primary(item)
    except FontLoadError:
        item.style.fallback_to_system_fonts()
        return await render_primary(item)
    except TimeoutError:
        item.reduce_complexity()
        return await render_primary(item)
```

### Monitoring & Diagnostics
```python
class RenderingMetrics:
    def __init__(self):
        self.render_times = []
        self.cache_hit_rate = 0.0
        self.error_count = 0
        self.memory_usage = []
    
    def record_render(self, duration: float, cache_hit: bool):
        self.render_times.append(duration)
        self.update_cache_hit_rate(cache_hit)
```

## Integration Points

### Template System Integration
```python
from ..template import TemplateLoader

template = TemplateLoader.load("hype")
css_style = template.get_css_for_word(word, context)
image = await renderer.render_word(word, css_style)
```

### Animation System Integration
```python
from ..animation import AnimationEngine

animation = AnimationEngine.get_animation("fadeIn")
frames = await renderer.render_animation(text, animation)
```

### Layout Engine Integration
```python
from ..layout import LayoutEngine

layout = LayoutEngine.calculate_positions(words)
images = await renderer.render_positioned_words(words, layout)
```

## Configuration Options

### Renderer Settings
```json
{
  "renderer": {
    "browser": {
      "type": "chromium",
      "headless": true,
      "viewport": {"width": 1920, "height": 1080}
    },
    "performance": {
      "max_concurrent_renders": 4,
      "render_timeout_ms": 10000,
      "memory_limit_mb": 2048
    },
    "cache": {
      "enabled": true,
      "max_size_mb": 500,
      "ttl_seconds": 3600
    },
    "quality": {
      "image_format": "PNG",
      "compression_quality": 95,
      "anti_aliasing": true
    }
  }
}
```

### Environment Variables
```bash
# Browser configuration
PYCAPS_BROWSER_EXECUTABLE="/path/to/chrome"
PYCAPS_BROWSER_ARGS="--no-sandbox,--disable-web-security"

# Performance settings
PYCAPS_MAX_RENDER_WORKERS=4
PYCAPS_RENDER_TIMEOUT=10000

# Cache configuration
PYCAPS_CACHE_DIR="/tmp/pycaps_cache"
PYCAPS_CACHE_SIZE_LIMIT=500
```

## Development Workflows

### Testing Renderer
```python
import pytest
from pycaps.renderer import CSSRenderer

@pytest.mark.asyncio
async def test_basic_rendering():
    renderer = CSSRenderer()
    try:
        style = {"font-size": "24px", "color": "red"}
        image = await renderer.render_word("Hello", style)
        assert image.size[0] > 0
        assert image.size[1] > 0
    finally:
        await renderer.close()
```

### Custom Style Development
```python
# Test custom styles
async def test_custom_style():
    style = {
        "font-family": "'Comic Sans MS'",
        "font-size": "48px",
        "background": "linear-gradient(45deg, red, blue)",
        "border-radius": "10px",
        "padding": "20px"
    }
    
    image = await renderer.render_word("Test", style)
    # Validate rendered output
```

### Performance Testing
```python
async def benchmark_rendering():
    words = ["Test"] * 100
    start_time = time.time()
    
    tasks = [renderer.render_word(word, style) for word in words]
    images = await asyncio.gather(*tasks)
    
    duration = time.time() - start_time
    print(f"Rendered {len(words)} words in {duration:.2f}s")
```

## Troubleshooting Guide

### Common Issues

1. **Playwright Installation Issues**
   ```bash
   # Install Playwright browsers
   playwright install chromium
   
   # Verify installation
   playwright --help
   ```

2. **Font Rendering Problems**
   ```python
   # Debug font loading
   css_debug = {
       "font-family": "Arial, sans-serif",  # Use system fonts
       "font-display": "swap"  # Ensure font fallback
   }
   ```

3. **Memory Issues**
   ```python
   # Reduce concurrent renders
   renderer_config = {
       "max_concurrent_renders": 2,
       "memory_limit_mb": 1024
   }
   ```

4. **Browser Crashes**
   ```python
   # Enable browser recovery
   renderer = CSSRenderer(auto_restart=True, max_retries=3)
   ```

### Debug Configuration
```json
{
  "debug": {
    "save_html_files": true,
    "save_intermediate_images": true,
    "browser_devtools": false,
    "verbose_logging": true
  }
}
```

## API Reference

### Core Classes
- **`CSSRenderer`** - Main rendering interface
- **`RenderItem`** - Input specification for rendering
- **`ProcessedImage`** - Rendered image with metadata
- **`RenderCache`** - Caching system interface

### Key Methods
- **`render_word(word, style)`** - Render single word
- **`render_line(line, style)`** - Render text line
- **`render_batch(items)`** - Batch rendering
- **`clear_cache()`** - Clear rendering cache

### Configuration Classes
- **`BrowserConfig`** - Browser settings
- **`RenderConfig`** - Rendering options
- **`CacheConfig`** - Caching configuration

---
*Renderer Module | CSS engine | Browser automation | High-quality typography*