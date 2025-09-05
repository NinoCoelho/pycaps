# AI Word Highlighting Refactor - Summary

## Problem Solved
The AI word highlighting system was falling back to hardcoded word lists that included common Portuguese function words like "mais" (more) and "sua" (your), causing them to be frequently and inappropriately highlighted in Portuguese subtitles.

## Changes Made

### 1. WordImportanceTagger (`src/pycaps/tag/tagger/word_importance_tagger.py`)
- **Added preset and content_type parameters** to the constructor
- **Enhanced AI prompt** to be language-aware and context-sensitive
- **Added language detection** to identify Portuguese, Spanish, French, or English
- **Implemented preset-specific guidance** for the AI model:
  - `minimal`: 2-3 essential words only
  - `balanced`: 4-5 key words with good rhythm
  - `aggressive`: 6-8 high-impact words
  - `professional`: 2-3 business-critical terms
  - `entertainment`: 5-7 engaging, fun words
- **Explicit exclusion rules** for common function words in each language
- **Holistic text analysis** considering audience, theme, and message

### 2. IntelligentEnhancement (`src/pycaps/ai/intelligent_enhancement.py`)
- **Removed manual fallback system** completely
- **Removed ManualWordTagger import** and usage
- **Made AI required** for word highlighting (no fallback)
- **Added preset parameter** to constructor
- **Pass preset to WordImportanceTagger** for context-aware highlighting

### 3. CapsPipelineBuilder (`src/pycaps/pipeline/caps_pipeline_builder.py`)
- **Updated with_ai_enhancements** to pass preset to IntelligentEnhancement

### 4. Removed Dependencies
- No longer imports or uses `ManualWordTagger`
- Removed hardcoded word lists for Portuguese/English

## Benefits

1. **No more inappropriate highlighting** of common function words
2. **Language-aware processing** that respects linguistic differences
3. **Context-sensitive selection** based on the actual message
4. **Preset-driven behavior** for different content types
5. **Better Portuguese support** without hardcoded bias

## Usage

```bash
# Use with professional preset to avoid excessive highlighting
pycaps render video.mp4 output.mp4 --ai-preset professional --ai-word-highlighting

# For entertainment content with more dynamic highlighting
pycaps render video.mp4 output.mp4 --ai-preset entertainment --ai-word-highlighting

# Minimal highlighting for clean subtitles
pycaps render video.mp4 output.mp4 --ai-preset minimal --ai-word-highlighting
```

## Requirements

- **OpenAI API Key is now required** for word highlighting to work
- Set environment variable: `export OPENAI_API_KEY='your-key-here'`
- Without AI, word highlighting is disabled (no fallback)

## Testing

A test script `test_ai_highlighting.py` has been created to validate the new system with both Portuguese and English text across different presets.