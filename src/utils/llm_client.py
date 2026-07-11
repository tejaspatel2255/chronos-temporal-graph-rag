from openai import OpenAI
from config.settings import settings

class LLMClient:
    def __init__(self):
        # OpenRouter base_url and api_key from settings
        self.client = OpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY
        )

    def completion(self, prompt: str, system_prompt: str = None, temperature: float = 0.2, model: str = "openrouter/free") -> str:
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
