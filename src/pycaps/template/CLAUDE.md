# Template Module - Claude Context

**Module Type:** Template System & Resource Management
**Primary Technologies:** JSON Configuration, CSS3, Resource Bundling, File Management
**Dependencies:** Pydantic, pathlib, json, typing
**Last Updated:** 2025-08-18

## Module Overview

The Template module provides a comprehensive template system for pycaps that packages styling, animations, effects, and configurations into reusable components. It manages 11 built-in templates and supports custom template creation with CSS bundling, resource management, and inheritance capabilities.

### Core Responsibilities
- Template loading and validation
- CSS and resource bundling
- Configuration inheritance and merging
- Built-in template library management
- Custom template creation and registration
- Asset pipeline and resource optimization

### Template Architecture
```
Template Structure:
├── template.json (configuration)
├── styles.css (main styling)
├── assets/ (images, fonts, media)
├── animations.json (animation definitions)
└── variants/ (template variations)
```

## Built-in Template Library

### Available Templates
1. **default** - Clean, professional styling
2. **minimalist** - Simple, understated design
3. **hype** - High-energy, vibrant effects
4. **retro-gaming** - Pixelated, arcade-style
5. **neon** - Glowing, cyberpunk aesthetic
6. **corporate** - Business-friendly styling
7. **social** - Social media optimized
8. **cinematic** - Movie-style subtitles
9. **comic** - Comic book styling
10. **elegant** - Sophisticated typography
11. **cyberpunk** - Futuristic, tech aesthetic

### Template Selection Strategy
```python
def select_template_for_content(content_type: str, platform: str) -> str:
    template_map = {
        ("entertainment", "tiktok"): "hype",
        ("entertainment", "youtube"): "cinematic", 
        ("business", "linkedin"): "corporate",
        ("education", "any"): "minimalist",
        ("gaming", "any"): "retro-gaming",
        ("tech", "any"): "cyberpunk"
    }
    return template_map.get((content_type, platform), "default")
```

## Core Components

### 1. Template Loader (`template_loader.py`)

**Purpose**: Load and manage templates with caching and validation
```python
class TemplateLoader:
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.cache = {}
        self.built_in_templates = self._discover_built_in_templates()
    
    def load(self, template_name: str) -> Template:
        """Load template with caching"""
        if template_name in self.cache:
            return self.cache[template_name]
        
        template_path = self._resolve_template_path(template_name)
        template = self._load_from_path(template_path)
        
        # Validate template
        self._validate_template(template)
        
        # Cache and return
        self.cache[template_name] = template
        return template
    
    def list_available_templates(self) -> List[str]:
        """List all available templates"""
        built_in = list(self.built_in_templates.keys())
        custom = self._discover_custom_templates()
        return built_in + custom
    
    def reload_template(self, template_name: str) -> Template:
        """Force reload template (bypass cache)"""
        if template_name in self.cache:
            del self.cache[template_name]
        return self.load(template_name)
```

### 2. Template Configuration (`template_config.py`)

**Purpose**: Define template structure and validation schema
```python
@dataclass
class TemplateConfig:
    name: str
    version: str
    description: str
    author: str
    
    # Styling configuration
    base_css: str
    fonts: List[FontConfig]
    colors: ColorPalette
    typography: TypographyConfig
    
    # Animation configuration
    animations: Dict[str, AnimationConfig]
    effects: List[EffectConfig]
    
    # Rendering settings
    rendering: RenderConfig
    
    # Template metadata
    preview_image: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    
    def merge_with(self, override_config: 'TemplateConfig') -> 'TemplateConfig':
        """Merge this template with override configuration"""
        merged = copy.deepcopy(self)
        
        # Merge CSS
        if override_config.base_css:
            merged.base_css = self._merge_css(merged.base_css, override_config.base_css)
        
        # Merge animations
        merged.animations.update(override_config.animations)
        
        # Merge other configurations
        merged.effects.extend(override_config.effects)
        
        return merged
```

### 3. Built-in Template Definitions

#### Default Template (`templates/default/template.json`)
```json
{
  "name": "default",
  "version": "1.0.0",
  "description": "Clean, professional subtitle styling",
  "author": "pycaps",
  "styling": {
    "base_css": "styles.css",
    "fonts": [
      {
        "family": "Inter",
        "weights": [400, 600, 700],
        "source": "google_fonts"
      }
    ],
    "colors": {
      "primary": "#ffffff",
      "secondary": "#f0f0f0",
      "accent": "#007acc",
      "background": "#000000",
      "shadow": "rgba(0,0,0,0.8)"
    },
    "typography": {
      "base_font_size": 48,
      "line_height": 1.2,
      "letter_spacing": "0.02em",
      "text_shadow": "2px 2px 4px var(--shadow-color)"
    }
  },
  "animations": {
    "entrance": {
      "type": "fade",
      "duration": 0.5,
      "timing": "ease-out"
    },
    "emphasis": {
      "type": "scale",
      "scale_factor": 1.1,
      "duration": 0.2
    },
    "exit": {
      "type": "fade",
      "duration": 0.3,
      "timing": "ease-in"
    }
  },
  "effects": [
    {
      "type": "word_emphasis",
      "intensity": 0.6,
      "triggers": ["important_words"]
    }
  ],
  "rendering": {
    "quality": "high",
    "anti_aliasing": true,
    "background_transparency": true
  },
  "platforms": ["youtube", "vimeo", "general"],
  "tags": ["professional", "clean", "versatile"]
}
```

#### Hype Template (`templates/hype/template.json`)
```json
{
  "name": "hype",
  "version": "1.0.0", 
  "description": "High-energy styling for viral content",
  "author": "pycaps",
  "styling": {
    "base_css": "hype-styles.css",
    "fonts": [
      {
        "family": "Montserrat",
        "weights": [700, 800, 900],
        "source": "google_fonts"
      }
    ],
    "colors": {
      "primary": "#ffffff",
      "accent": "#ff6b6b",
      "secondary": "#4ecdc4", 
      "gradient_start": "#ff6b6b",
      "gradient_end": "#4ecdc4",
      "shadow": "rgba(255,107,107,0.8)"
    },
    "typography": {
      "base_font_size": 56,
      "font_weight": 800,
      "text_transform": "uppercase",
      "letter_spacing": "0.05em",
      "text_shadow": "3px 3px 6px var(--shadow-color)"
    }
  },
  "animations": {
    "entrance": {
      "type": "composite",
      "animations": [
        {"type": "pop_in", "intensity": 1.5},
        {"type": "glow", "color": "#ff6b6b"}
      ]
    },
    "emphasis": {
      "type": "bounce",
      "intensity": 1.2,
      "duration": 0.4
    },
    "word_reveal": {
      "type": "typewriter",
      "speed": 20
    }
  },
  "effects": [
    {
      "type": "emoji_insertion",
      "intensity": 0.8,
      "emoji_set": "energy"
    },
    {
      "type": "caps_emphasis", 
      "intensity": 1.0
    },
    {
      "type": "exclamation_boost",
      "scale_factor": 1.3
    }
  ],
  "platforms": ["tiktok", "instagram", "youtube_shorts"],
  "tags": ["energetic", "viral", "social_media", "bold"]
}
```

### 4. CSS Management (`css_manager.py`)

**Purpose**: Handle CSS compilation, optimization, and injection
```python
class CSSManager:
    def __init__(self, template_path: Path):
        self.template_path = template_path
        self.css_cache = {}
    
    def compile_css(self, template_config: TemplateConfig) -> str:
        """Compile complete CSS from template configuration"""
        css_parts = []
        
        # Load base CSS file
        base_css_path = self.template_path / template_config.base_css
        if base_css_path.exists():
            css_parts.append(base_css_path.read_text())
        
        # Generate CSS from configuration
        css_parts.append(self._generate_typography_css(template_config.typography))
        css_parts.append(self._generate_color_css(template_config.colors))
        css_parts.append(self._generate_animation_css(template_config.animations))
        
        # Process CSS variables and functions
        compiled_css = "\n".join(css_parts)
        compiled_css = self._process_css_variables(compiled_css, template_config)
        compiled_css = self._optimize_css(compiled_css)
        
        return compiled_css
    
    def _generate_typography_css(self, typography: TypographyConfig) -> str:
        """Generate typography CSS rules"""
        return f"""
        .subtitle-word {{
            font-size: {typography.base_font_size}px;
            line-height: {typography.line_height};
            letter-spacing: {typography.letter_spacing};
            text-shadow: {typography.text_shadow};
            font-weight: {typography.font_weight};
        }}
        """
    
    def _generate_color_css(self, colors: ColorPalette) -> str:
        """Generate CSS custom properties for colors"""
        css_vars = []
        for name, value in colors.items():
            css_vars.append(f"--{name.replace('_', '-')}: {value};")
        
        return f"""
        :root {{
            {chr(10).join(css_vars)}
        }}
        """
```

### 5. Resource Management (`resource_manager.py`)

**Purpose**: Handle fonts, images, and other template assets
```python
class ResourceManager:
    def __init__(self, template_path: Path):
        self.template_path = template_path
        self.asset_cache = {}
    
    def load_fonts(self, font_configs: List[FontConfig]) -> List[FontResource]:
        """Load and cache font resources"""
        fonts = []
        for config in font_configs:
            font = self._load_font(config)
            fonts.append(font)
        return fonts
    
    def _load_font(self, config: FontConfig) -> FontResource:
        """Load individual font resource"""
        if config.source == "google_fonts":
            return self._load_google_font(config)
        elif config.source == "local":
            return self._load_local_font(config)
        elif config.source == "url":
            return self._load_web_font(config)
    
    def _load_google_font(self, config: FontConfig) -> FontResource:
        """Load font from Google Fonts"""
        weights_str = ":wght@" + ";".join(map(str, config.weights))
        font_url = f"https://fonts.googleapis.com/css2?family={config.family.replace(' ', '+')}{weights_str}&display=swap"
        
        return FontResource(
            family=config.family,
            url=font_url,
            weights=config.weights,
            format="woff2"
        )
    
    def bundle_assets(self, template_name: str) -> AssetBundle:
        """Create optimized asset bundle for template"""
        template_dir = self.template_path / template_name
        
        # Collect all assets
        css_files = list(template_dir.glob("*.css"))
        image_files = list(template_dir.glob("assets/*.{png,jpg,jpeg,gif,webp}"))
        font_files = list(template_dir.glob("assets/fonts/*"))
        
        # Create bundle
        bundle = AssetBundle(
            css=self._bundle_css_files(css_files),
            images=self._optimize_images(image_files),
            fonts=self._bundle_fonts(font_files)
        )
        
        return bundle
```

### 6. Template Inheritance (`template_inheritance.py`)

**Purpose**: Support template inheritance and composition
```python
class TemplateInheritance:
    def __init__(self, loader: TemplateLoader):
        self.loader = loader
    
    def create_derived_template(
        self, 
        base_template: str, 
        overrides: Dict[str, Any],
        name: str
    ) -> Template:
        """Create new template by inheriting from base template"""
        
        # Load base template
        base = self.loader.load(base_template)
        
        # Apply overrides
        derived_config = self._apply_overrides(base.config, overrides)
        
        # Create new template
        derived = Template(
            name=name,
            config=derived_config,
            base_template=base_template
        )
        
        return derived
    
    def _apply_overrides(self, base_config: TemplateConfig, overrides: Dict) -> TemplateConfig:
        """Apply override configuration to base template"""
        merged = copy.deepcopy(base_config)
        
        # Handle nested overrides
        for key, value in overrides.items():
            if key == "styling":
                merged.styling = self._merge_styling(merged.styling, value)
            elif key == "animations":
                merged.animations.update(value)
            elif key == "effects":
                merged.effects.extend(value)
            else:
                setattr(merged, key, value)
        
        return merged
```

## Template Development Workflow

### Creating Custom Templates

#### 1. Template Directory Structure
```
custom_template/
├── template.json          # Configuration
├── styles.css            # Main CSS
├── assets/              # Static assets
│   ├── fonts/          # Custom fonts
│   ├── images/         # Template images
│   └── sounds/         # Audio assets
├── variants/           # Template variations
│   ├── dark.json      # Dark variant
│   └── light.json     # Light variant
└── preview.png        # Template preview
```

#### 2. Template Configuration
```json
{
  "name": "my_custom_template",
  "version": "1.0.0",
  "description": "My awesome custom template",
  "author": "Your Name",
  "base_template": "default",  // Optional inheritance
  "styling": {
    // Custom styling configuration
  },
  "animations": {
    // Custom animations
  },
  "effects": [
    // Custom effects
  ]
}
```

#### 3. CSS Development
```css
/* styles.css */
.subtitle-word {
    font-family: 'CustomFont', sans-serif;
    font-size: var(--base-font-size, 48px);
    color: var(--primary-color, #ffffff);
    
    /* Custom styling */
    background: linear-gradient(45deg, var(--gradient-start), var(--gradient-end));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    
    /* Animation support */
    transition: all 0.3s ease;
}

.subtitle-word.emphasized {
    transform: scale(1.2);
    filter: drop-shadow(0 0 10px var(--accent-color));
}
```

### Template Testing
```python
def test_custom_template():
    # Load template
    loader = TemplateLoader(template_dir)
    template = loader.load("my_custom_template")
    
    # Validate configuration
    assert template.config.name == "my_custom_template"
    assert template.config.version == "1.0.0"
    
    # Test CSS compilation
    css = template.compile_css()
    assert ".subtitle-word" in css
    
    # Test resource loading
    resources = template.load_resources()
    assert len(resources.fonts) > 0
```

## Template API

### Template Class (`template.py`)
```python
class Template:
    def __init__(self, name: str, config: TemplateConfig, path: Path):
        self.name = name
        self.config = config
        self.path = path
        self.css_manager = CSSManager(path)
        self.resource_manager = ResourceManager(path)
    
    def get_css_for_element(self, element: Element, context: RenderContext) -> str:
        """Get compiled CSS for specific element"""
        base_css = self.css_manager.compile_css(self.config)
        element_css = self._generate_element_css(element, context)
        return base_css + "\n" + element_css
    
    def get_animation_config(self, animation_name: str) -> Optional[AnimationConfig]:
        """Get animation configuration by name"""
        return self.config.animations.get(animation_name)
    
    def get_effect_configs(self) -> List[EffectConfig]:
        """Get all effect configurations"""
        return self.config.effects
    
    def create_variant(self, variant_name: str, overrides: Dict) -> 'Template':
        """Create template variant with overrides"""
        variant_config = self.config.merge_with(overrides)
        return Template(
            name=f"{self.name}_{variant_name}",
            config=variant_config,
            path=self.path
        )
```

## Configuration Reference

### Template JSON Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "version": {"type": "string"},
    "description": {"type": "string"},
    "author": {"type": "string"},
    "base_template": {"type": "string"},
    "styling": {
      "type": "object",
      "properties": {
        "base_css": {"type": "string"},
        "fonts": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "family": {"type": "string"},
              "weights": {"type": "array", "items": {"type": "integer"}},
              "source": {"enum": ["google_fonts", "local", "url"]}
            }
          }
        },
        "colors": {
          "type": "object",
          "additionalProperties": {"type": "string"}
        },
        "typography": {
          "type": "object",
          "properties": {
            "base_font_size": {"type": "integer"},
            "line_height": {"type": "number"},
            "letter_spacing": {"type": "string"},
            "font_weight": {"type": "integer"},
            "text_shadow": {"type": "string"}
          }
        }
      }
    },
    "animations": {
      "type": "object",
      "additionalProperties": {
        "type": "object"
      }
    },
    "effects": {
      "type": "array",
      "items": {"type": "object"}
    }
  },
  "required": ["name", "version", "description", "author"]
}
```

## Performance Optimization

### Template Caching
```python
class TemplateCache:
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
    
    def get(self, template_name: str) -> Optional[Template]:
        if template_name in self.cache:
            self.access_times[template_name] = time.time()
            return self.cache[template_name]
        return None
    
    def put(self, template_name: str, template: Template):
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[template_name] = template
        self.access_times[template_name] = time.time()
```

### CSS Optimization
```python
def optimize_template_css(css: str) -> str:
    # Remove comments and unnecessary whitespace
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    css = re.sub(r'\s+', ' ', css)
    
    # Combine similar selectors
    css = combine_similar_selectors(css)
    
    # Remove duplicate properties
    css = remove_duplicate_properties(css)
    
    return css.strip()
```

## Integration Points

### Pipeline Integration
```python
from ..pipeline import CapsPipeline

# Templates are loaded during pipeline configuration
pipeline = CapsPipeline.from_template("hype")
```

### Renderer Integration
```python
from ..renderer import CSSRenderer

# Templates provide CSS for rendering
template = template_loader.load("cinematic")
css = template.get_css_for_element(word, context)
image = await renderer.render_with_css(word.text, css)
```

### CLI Integration
```python
# CLI template management commands
pycaps template list                    # List available templates
pycaps template preview hype           # Preview template
pycaps template install custom.zip     # Install custom template
pycaps template create my_template     # Create new template
```

## Troubleshooting Guide

### Common Issues

1. **Template Not Found**
   ```python
   # Check available templates
   loader = TemplateLoader(template_dir)
   available = loader.list_available_templates()
   print(f"Available templates: {available}")
   ```

2. **CSS Compilation Errors**
   ```python
   # Debug CSS compilation
   try:
       css = template.compile_css()
   except CSSCompilationError as e:
       print(f"CSS error: {e}")
       print(f"Line: {e.line_number}")
   ```

3. **Font Loading Issues**
   ```python
   # Check font availability
   resources = template.load_resources()
   for font in resources.fonts:
       if not font.is_available():
           print(f"Font not available: {font.family}")
   ```

4. **Resource Bundle Size**
   ```python
   # Monitor bundle size
   bundle = resource_manager.bundle_assets(template_name)
   total_size = bundle.get_total_size()
   if total_size > MAX_BUNDLE_SIZE:
       print(f"Bundle too large: {total_size} bytes")
   ```

## API Reference

### Core Classes
- **`TemplateLoader`** - Template loading and management
- **`Template`** - Template instance with configuration
- **`TemplateConfig`** - Template configuration schema
- **`CSSManager`** - CSS compilation and optimization
- **`ResourceManager`** - Asset management

### Key Methods
- **`TemplateLoader.load(name)`** - Load template by name
- **`Template.get_css_for_element(element, context)`** - Get element CSS
- **`Template.create_variant(name, overrides)`** - Create template variant
- **`CSSManager.compile_css(config)`** - Compile template CSS

---
*Template Module | Styling system | Asset management | Configuration framework*