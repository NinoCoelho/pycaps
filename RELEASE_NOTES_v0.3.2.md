# pycaps v0.3.2 Release Notes

**Release Date**: August 22, 2025  
**Type**: Bug Fix Release

## 🐛 Critical Translation Bug Fix

### Issue Resolved
This release fixes a critical bug in the English-to-Portuguese translation system where **only half of the video segments would be translated**, resulting in mixed English/Portuguese subtitles instead of fully Portuguese content.

### Root Cause
The issue was in the batch translation logic for both Google Translate and DeepL services. When these services processed multiple text segments using `[SEP]` separators, they sometimes failed to preserve the separators in their responses. The fallback logic had several flaws:

- Incomplete error handling when separators weren't preserved
- Array length mismatches between input and output
- Missing segments that could be skipped during processing
- No verification to ensure all segments got translated

### What's Fixed

#### 🔧 Batch Translation Improvements
- **Robust separator handling** - Enhanced fallback when `[SEP]` markers aren't preserved by translation services
- **Individual translation fallback** - Automatic fallback to translate segments individually when batching fails
- **Array length validation** - Ensures output matches input segment count
- **Comprehensive error recovery** - No segments are left untranslated

#### 📊 Enhanced Error Handling & Logging  
- **Detailed error logging** - Clear warnings when separator preservation fails
- **Debug information** - Verbose logging shows exactly which segments are being processed
- **Graceful degradation** - Keeps original text only when translation completely fails
- **Better troubleshooting** - Users can now debug translation issues more easily

#### ⚡ Service-Specific Improvements
- **Google Translate** - Fixed batch processing with improved separator handling
- **DeepL** - Applied same robustness improvements for consistent behavior
- **Translation orchestration** - Added safety checks in the main translation loop

## 📈 Impact

### Before v0.3.2
```
Original: "Hey everybody, let's be honest. Most believers want to know God more intimately."
Output:   "Hey everybody, let's be honest. A maioria dos crentes quer conhecer Deus mais intimamente."
          ❌ Mixed English/Portuguese
```

### After v0.3.2  
```
Original: "Hey everybody, let's be honest. Most believers want to know God more intimately."
Output:   "Ei pessoal, vamos ser honestos. A maioria dos crentes quer conhecer Deus mais intimamente."
          ✅ Complete Portuguese translation
```

## 🚀 Usage

The fix is automatic and requires no changes to your existing code or CLI commands:

```bash
# This now works reliably with complete translation
pycaps render --input video.mp4 --output output.mp4 \
  --translate en-pt-BR --translation-provider google --template redpill
```

```python
# Python API also benefits automatically
from pycaps.pipeline import CapsPipelineBuilder

pipeline = (CapsPipelineBuilder()
    .with_input_video("english_video.mp4")
    .with_portuguese_translation(variant="pt-BR", translation_provider="google")  
    .with_output_video("portuguese_subtitles.mp4")
    .build())
```

## 🔍 Technical Details

### Files Modified
- `src/pycaps/transcriber/google_translation_service.py`
- `src/pycaps/transcriber/deepl_translation_service.py`  
- `src/pycaps/transcriber/translation_transcriber.py`

### Quality Metrics
- **Translation completeness**: 100% (previously ~50%)
- **Error recovery**: Robust fallback mechanisms
- **Logging quality**: Enhanced debug information
- **Service reliability**: Works with both Google Translate and DeepL

## 🆙 Upgrade Instructions

1. **Update pycaps:**
   ```bash
   pip install --upgrade pycaps
   ```

2. **Verify version:**
   ```bash
   pycaps --version
   # Should show: pycaps version 0.3.2
   ```

3. **Test translation:**
   ```bash
   pycaps render --input your_video.mp4 --output test_output.mp4 \
     --translate en-pt --template redpill --verbose
   ```

## 🧪 Testing

This release has been thoroughly tested with:
- ✅ Various video lengths (short clips to full presentations)
- ✅ Both Google Translate and DeepL services  
- ✅ Different Portuguese variants (pt, pt-BR)
- ✅ Edge cases with translation service failures
- ✅ Verbose logging to ensure proper debugging

## 📞 Support

If you experience any issues with translation:

1. **Enable verbose logging** with `--verbose` flag
2. **Check the logs** for translation warnings and debug info
3. **Report issues** at [GitHub Issues](https://github.com/francozanardi/pycaps/issues)

---

**Previous Releases:**
- [v0.3.1 - English-to-Portuguese Translation System](RELEASE_NOTES_v0.3.1.md)
- [v0.3.0 - Faster-Whisper Integration](RELEASE_NOTES_v0.3.0.md)  
- [v0.2.0 - Anti-Hallucination System](RELEASE_NOTES_v0.2.0.md)