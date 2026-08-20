from openai import OpenAI
from config.settings import settings
import sys

# Active provider state
ACTIVE_PROVIDER = "openrouter"
PROVIDER_OVERRIDE = None

PROVIDERS_CONFIG = {
    "openrouter": {
        "name": "OpenRouter (Primary - Llama 3.3 70B)",
        "base_url": settings.OPENROUTER_BASE_URL,
        "api_key": settings.OPENROUTER_API_KEY,
        "default_model": settings.OPENROUTER_MODEL,
        "extra_headers": {
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "Project Chronos"
        }
    },
    "groq": {
        "name": "Groq (Fallback - Llama 3.3 70B)",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": settings.GROQ_API_KEY,
        "default_model": settings.GROQ_MODEL,
        "extra_headers": {}
    }
}

def get_active_provider_info():
    global ACTIVE_PROVIDER, PROVIDER_OVERRIDE
    provider_key = PROVIDER_OVERRIDE or ACTIVE_PROVIDER
    if provider_key not in PROVIDERS_CONFIG:
        provider_key = "openrouter"
    return provider_key, PROVIDERS_CONFIG[provider_key]

def set_active_provider(provider_key: str):
    global ACTIVE_PROVIDER
    if provider_key in PROVIDERS_CONFIG:
        ACTIVE_PROVIDER = provider_key
        print(f"[*] [LLM Client] Switched primary active provider to: '{provider_key}'")
        return True
    return False

class LLMClient:
    def __init__(self, provider: str = None):
        provider_key, config = get_active_provider_info()
        if provider and provider in PROVIDERS_CONFIG:
            provider_key = provider
            config = PROVIDERS_CONFIG[provider]

        self.provider_key = provider_key
        self.config = config

    def completion(self, prompt: str, system_prompt: str = None, temperature: float = 0.2, model: str = None) -> str:
        provider_key, config = get_active_provider_info()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Strict order: Active provider first, then Groq fallback if active is openrouter (or openrouter if active is groq)
        fallback_order = [provider_key] + [p for p in ["openrouter", "groq"] if p != provider_key]

        last_error = None
        for p_key in fallback_order:
            p_config = PROVIDERS_CONFIG[p_key]
            
            # Skip provider if API key is not configured
            if not p_config["api_key"]:
                print(f"[*] [LLM Fallback] Skipping '{p_key}' because API key is not set.", file=sys.stderr)
                continue

            try:
                client = OpenAI(
                    base_url=p_config["base_url"],
                    api_key=p_config["api_key"]
                )
                m_model = p_config["default_model"] if (p_key != provider_key or not model) else model
                
                kwargs = {
                    "model": m_model,
                    "messages": messages,
                    "temperature": temperature
                }
                if p_config.get("extra_headers"):
                    kwargs["extra_headers"] = p_config["extra_headers"]

                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
            except Exception as err:
                print(f"[WARNING] [LLM Fallback] Provider '{p_key}' failed: {err}. Attempting next provider in fallback chain...", file=sys.stderr)
                last_error = err

        raise RuntimeError(f"All configured LLM Providers (OpenRouter/Groq) failed. Last error: {last_error}")

def validate_llm_connectivity():
    """Performs a lightweight validation check to confirm active LLM provider connectivity."""
    p_key, config = get_active_provider_info()
    print(f"[*] [Startup Check] Initializing model connection to provider: '{p_key}' ({config['default_model']})")
    try:
        client = LLMClient()
        response = client.completion(
            prompt="ok",
            temperature=0.0
        )
        if not response or not response.strip():
            raise ValueError("LLM returned an empty or invalid response.")
        print(f"[*] [Startup Check] LLM validation successful. Active Provider: '{p_key}'")
    except Exception as e:
        print(f"[WARNING] LLM Startup Connection Check Warning for provider '{p_key}': {e}", file=sys.stderr)
        print("[WARNING] The server will start, but queries requiring LLM will depend on active OpenRouter/Groq API keys.", file=sys.stderr)
