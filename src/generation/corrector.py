from src.generation.prompts import CORRECTION_PROMPT, build_correction_prompt

def rewrite_query(original_query: str, validation_result: dict, llm_client) -> str:
    """Rewrites the original search query based on validation failures to improve recall."""
    prompt = build_correction_prompt(original_query, validation_result)
    
    try:
        response = llm_client.completion(
            prompt=prompt,
            system_prompt=CORRECTION_PROMPT,
            temperature=0.7
        )
        return response.strip()
    except Exception as e:
        print(f"[ERROR] Query rewriting failed: {e}. Falling back to original.")
        return original_query
