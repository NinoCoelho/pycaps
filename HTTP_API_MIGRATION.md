# OpenAI HTTP API Migration Summary

## Changes Made

### 1. Replaced OpenAI Client with HTTP Calls (`src/pycaps/ai/gpt.py`)
- **Removed**: `openai` package dependency
- **Added**: Direct HTTP calls using `requests`
- **Added**: Proper error handling for HTTP requests
- **Added**: Session management for better performance
- **Added**: Custom User-Agent header

### 2. Updated Dependencies (`pyproject.toml`)
- **Removed**: `openai>=1.0.0` dependency
- **Kept**: `requests` (already in dependencies)

### 3. Enhanced Configuration (`.env.sample`)
- **Added**: Examples for different API endpoints (OpenRouter, etc.)

## Benefits

1. **No OpenAI Package Conflicts**: Eliminates version compatibility issues
2. **Lighter Dependencies**: One less package to manage
3. **Full Control**: Direct control over HTTP requests and timeouts
4. **Better Error Messages**: More specific error handling
5. **Compatible with Any API**: Works with OpenAI, OpenRouter, or any OpenAI-compatible API

## HTTP Implementation Details

### API Endpoint
- Default: `https://api.openai.com/v1/chat/completions`
- Configurable via `OPENAI_BASE_URL` environment variable

### Request Format
```json
{
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "prompt"}],
  "max_tokens": 1000,
  "temperature": 0.1
}
```

### Headers
```http
Authorization: Bearer {OPENAI_API_KEY}
Content-Type: application/json
User-Agent: pycaps/0.3.6
```

### Error Handling
- HTTP request errors (network, timeout)
- API response parsing errors
- Missing API key validation
- Rate limiting and error responses

## Testing

Use the test script to verify the implementation:

```bash
export OPENAI_API_KEY='your-key-here'
python test_http_ai.py
```

## Usage (Unchanged)

The API usage remains the same:

```bash
# Test AI highlighting with HTTP-based implementation
export OPENAI_API_KEY='your-key-here'
pycaps render sample.mp4 output.mp4 --ai-preset professional --ai-word-highlighting
```

## Compatibility

- ✅ **OpenAI API**: Full compatibility
- ✅ **OpenRouter**: Set `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
- ✅ **Other Compatible APIs**: Any service supporting OpenAI Chat Completions format
- ✅ **Custom Models**: Set `PYCAPS_AI_MODEL=your-model-name`

## Migration Benefits

This migration solves the original error and provides a more robust, dependency-light solution for AI functionality.