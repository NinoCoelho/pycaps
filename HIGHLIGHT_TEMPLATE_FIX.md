# RedPill Template Highlight Fix

## Problem Identified

The AI was correctly identifying and tagging multiple words for highlighting:
- `'transformam' (highlight)` 
- `'vaidade' (highlight)`
- `'influenciar' (highlight)`
- `'liderança' (emphasis)` (multiple times)

However, only `'liderança'` was showing up highlighted in the final video because **the redpill template was missing CSS styles for `.word.highlight` class**.

## Root Cause

The redpill template (`src/pycaps/template/preset/redpill/styles.css`) only had CSS definitions for:
- `.word.emphasis` ← **Had styling** (gold text, bright red background, larger size)
- `.word.highlight` ← **Missing styling** (no visual effect)

## Solution Applied

Added complete CSS styling for highlight words to the redpill template:

### Added Styles:
```css
/* Highlight words (medium importance) */
.word.highlight.word-being-narrated {
    font-size: 4.2vw !important;
    background-color: #cc3300 !important;  /* Darker red */
    color: #ffffff !important;
    border-radius: 1.25vw;
    padding: 0.7vw 0.5vw;
    text-shadow: 
        0 0 1.5vw #cc3300,
        0 0.2vw 0.4vw rgba(0, 0, 0, 0.8);
    animation: highlight-pulse 2s ease-in-out infinite;
}

/* Other states */
.word.highlight.word-not-narrated-yet,
.word.highlight.word-already-narrated {
    font-size: 3.8vw !important;
    color: #ffcccc !important;
}

/* Animation */
@keyframes highlight-pulse {
    0%, 100% { 
        transform: scale(1);
        box-shadow: 0 0 0.8vw rgba(204,51,0,0.4);
    }
    50% { 
        transform: scale(1.02);
        box-shadow: 0 0 1.2vw rgba(204,51,0,0.7);
    }
}
```

## Visual Hierarchy

Now the redpill template has proper visual hierarchy:

1. **Emphasis words** (high importance):
   - 🔴 Bright red background (`#ff0000`)
   - ✨ Gold text (`#FFD700`)
   - 📏 Larger font size (5vw)
   - 🎭 Stronger glow effect

2. **Highlight words** (medium importance):
   - 🟤 Darker red background (`#cc3300`)
   - ⚪ White text (`#ffffff`)
   - 📏 Medium font size (4.2vw)
   - 🎭 Pulse animation

## Expected Result

After this fix, all AI-identified words should be visible:
- ✅ `transformam` → dark red highlight
- ✅ `liderança` → bright red emphasis (multiple instances)
- ✅ `vaidade` → dark red highlight  
- ✅ `influenciar` → dark red highlight

## Test Command

```bash
pycaps render --input sample.mp4 --output output.mp4 --template redpill --ai-word-highlighting
```

All 7 tagged words should now be visually highlighted in the final video!