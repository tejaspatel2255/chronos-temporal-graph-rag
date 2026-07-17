from src.generation.prompts import CORRECTION_PROMPT, build_correction_prompt

def rewrite_query(original_query: str, validation_result: dict, llm_client) -> str:
    """Rewrites the original search query based on validation failures to improve recall."""
    prompt = build_correction_prompt(original_query, validation_result)
    
    from src.utils.output_validation import is_degenerate_output
    
    for attempt in range(2):
        try:
            response = llm_client.completion(
                prompt=prompt,
                system_prompt=CORRECTION_PROMPT,
                temperature=0.7
            )
            candidate = response.strip()
            if is_degenerate_output(candidate):
                print(f"[WARNING] Rewritten query failed sanity check (attempt {attempt + 1}): '{candidate}'. Retrying...")
                continue
            return candidate
        except Exception as e:
            print(f"[WARNING] Query rewriting attempt {attempt + 1} failed: {e}")
            
    print("[WARNING] Query rewriting failed all sanity checks or errored. Falling back to original query.")
    return original_query

