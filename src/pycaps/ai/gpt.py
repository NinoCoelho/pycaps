from pycaps.ai.llm import Llm
import os

class Gpt(Llm):

    def __init__(self):
        self._client = None

    def send_message(self, prompt: str, model: str = None) -> str:
        if model is None:
            model = self._get_default_model()
        
        response = self._get_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1
        )
        return response.choices[0].message.content
    
    def is_enabled(self) -> bool:
        return os.getenv("OPENAI_API_KEY") is not None

    def _get_default_model(self) -> str:
        return os.getenv("PYCAPS_AI_MODEL", "gpt-4o-mini")

    def _get_client(self):
        try:
            from openai import OpenAI

            if self._client:
                return self._client

            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL")
            
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
