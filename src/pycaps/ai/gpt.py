from pycaps.ai.llm import Llm
import os
import json
import requests

class Gpt(Llm):

    def __init__(self):
        self._session = None

    def send_message(self, prompt: str, model: str = None) -> str:
        if model is None:
            model = self._get_default_model()
        
        # Prepare the request
        session = self._get_session()
        url = self._get_api_url()
        headers = self._get_headers()
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        try:
            response = session.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HTTP request failed: {e}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected API response format: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse API response: {e}")
    
    def is_enabled(self) -> bool:
        # Check if AI functionality is explicitly disabled
        ai_enabled = os.getenv("PYCAPS_AI_ENABLED", "true").lower()
        if ai_enabled in ("false", "0", "no", "off"):
            return False
        
        # AI is enabled if API key is available
        return os.getenv("OPENAI_API_KEY") is not None

    def _get_default_model(self) -> str:
        return os.getenv("PYCAPS_AI_MODEL", "gpt-4o-mini")

    def _get_session(self):
        """Get or create HTTP session for API requests."""
        if self._session is None:
            self._session = requests.Session()
        return self._session
    
    def _get_api_url(self) -> str:
        """Get the API endpoint URL."""
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        # Ensure base_url doesn't end with slash and add /chat/completions
        base_url = base_url.rstrip("/")
        return f"{base_url}/chat/completions"
    
    def _get_headers(self) -> dict:
        """Get HTTP headers for API requests."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is required\n\n"
                "Please set your OpenAI API key:\n"
                "export OPENAI_API_KEY='your-key-here'\n\n"
                "Optionally set OPENAI_BASE_URL for compatible APIs like OpenRouter.\n"
                "Optionally set PYCAPS_AI_MODEL to specify the model."
            )
        
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "pycaps/0.3.6"
        }
