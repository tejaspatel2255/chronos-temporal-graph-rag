import json
from src.generation.prompts import VALIDATION_PROMPT, build_validation_prompt

def validate_answer(draft_answer: str, context_chunks: list[dict], llm_client) -> dict:
    """Validates the draft answer against the retrieved context chunks using LLM evaluation."""
    prompt = build_validation_prompt(draft_answer, context_chunks)
    
    def clean_and_parse(response_text: str) -> dict:
        cleaned = response_text.strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        return json.loads(cleaned)

    try:
        response = llm_client.completion(prompt=prompt, system_prompt=VALIDATION_PROMPT)
        return clean_and_parse(response)
    except Exception as e:
        print(f"[WARNING] First validation attempt failed: {e}. Retrying once...")
        try:
            response = llm_client.completion(prompt=prompt, system_prompt=VALIDATION_PROMPT)
            return clean_and_parse(response)
        except Exception as retry_err:
            print(f"[ERROR] Repeated validation failure: {retry_err}")
            return {
                "is_supported": False,
                "hallucinated_claims": ["Unable to validate claims due to JSON parser errors."],
                "completeness": 0,
                "confidence": 0,
                "reasoning": f"Validation failed with error: {retry_err}"
            }
