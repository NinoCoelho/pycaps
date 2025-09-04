from pycaps.ai.llm import Llm
import os

class Gpt(Llm):

    def __init__(self):
        self._client = None

    def send_message(self, prompt: str, model: str = None) -> str:
        if model is None:
            model = self._get_default_model()
        
        import openai
        # Check if this is the old API (v0.x) or new API (v1.x)
        if hasattr(openai, 'ChatCompletion'):
            # Old API (v0.x)
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            return response.choices[0].message.content
        else:
            # New API (v1.x)
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            return response.choices[0].message.content
    
    def is_enabled(self) -> bool:
        # Check if AI functionality is explicitly disabled
        ai_enabled = os.getenv("PYCAPS_AI_ENABLED", "true").lower()
        if ai_enabled in ("false", "0", "no", "off"):
            return False
        
        # AI is enabled if API key is available
        return os.getenv("OPENAI_API_KEY") is not None

    def _get_default_model(self) -> str:
        return os.getenv("PYCAPS_AI_MODEL", "gpt-4o-mini")

    def _get_client(self):
        try:
            import openai
            
            # Set up OpenAI configuration based on API version
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            
            if hasattr(openai, 'ChatCompletion'):
                # Old API (v0.x) - configure globally
                openai.api_key = api_key
                if base_url:
                    openai.api_base = base_url
                return None  # No client needed for old API
            else:
                # New API (v1.x) - use client
                from openai import OpenAI
                
                if self._client:
                    return self._client

                if base_url:
                    self._client = OpenAI(api_key=api_key, base_url=base_url)
                else:
                    self._client = OpenAI(api_key=api_key)
                
                return self._client
        except ImportError:
            raise ImportError(
                "OpenAI API not found. "
                "Please install it with: pip install openai"
            )
        except Exception as e:
            raise RuntimeError(
                f"Error initializing OpenAI client: {e}\n\n"
                "Please ensure you have set OPENAI_API_KEY environment variable.\n"
                "Optionally set OPENAI_BASE_URL for compatible APIs like OpenRouter.\n"
                "Optionally set PYCAPS_AI_MODEL to specify the model."
            )
