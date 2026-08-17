from openai import OpenAI
from config.settings import settings

class LLMClient:
    def __init__(self):
        # OpenRouter base_url and api_key from settings
        self.client = OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY
        )

    def completion(self, prompt: str, system_prompt: str = None, temperature: float = 0.2, model: str = None) -> str:
        if model is None:
            model = settings.OPENROUTER_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Set default headers for OpenRouter (required/recommended by OpenRouter)
        extra_headers = {
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "Project Chronos"
        }

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            extra_headers=extra_headers
        )
        return response.choices[0].message.content

def validate_llm_connectivity():
    """Performs a lightweight validation check to confirm OpenRouter and the configured model are accessible."""
    import sys
    # Import settings locally to avoid circular dependencies
    from config.settings import settings
    print(f"[*] [Startup Check] Initializing model connection to: '{settings.OPENROUTER_MODEL}'")
    try:
        client = LLMClient()
        response = client.completion(
            prompt="ok",
            temperature=0.0
        )
        if not response or not response.strip():
            raise ValueError("LLM returned an empty or invalid response.")
        print(f"[*] [Startup Check] LLM validation successful. Active Model: '{settings.OPENROUTER_MODEL}'")
    except Exception as e:
        print(f"[WARNING] LLM Startup Connection Check Warning for '{settings.OPENROUTER_MODEL}': {e}", file=sys.stderr)
        print("[WARNING] The server will start, but queries requiring OpenRouter LLM will depend on active API keys.", file=sys.stderr)

