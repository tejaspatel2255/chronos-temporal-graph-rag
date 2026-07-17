import re
from src.generation.prompts import SYSTEM_PROMPT, build_generation_prompt

def generate_draft(query: str, context_chunks: list[dict], llm_client) -> dict:
    """Generates a draft answer using OpenRouter and extracts inline source citations."""
    prompt = build_generation_prompt(query, context_chunks)
    
    for attempt in range(2):
        try:
            response = llm_client.completion(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3
            )
            
            from src.utils.output_validation import is_degenerate_output
            if is_degenerate_output(response):
                print(f"[WARNING] Generated answer failed sanity check (attempt {attempt + 1}): '{response}'. Retrying...")
                continue
            
            # Extract citations using regex: [source: filename, chunk: id]
            matches = re.findall(r"\[source:\s*([^,\]]+),\s*chunk:\s*([^\]]+)\]", response)
            citations = []
            for match in matches:
                citations.append({
                    "source": match[0].strip(),
                    "chunk_id": match[1].strip()
                })
                
            return {
                "answer": response,
                "raw_citations": citations
            }
        except Exception as e:
            print(f"[WARNING] Answer generation attempt {attempt + 1} failed: {e}")
            if attempt == 1:
                return {
                    "answer": "Failed to generate an answer due to an internal LLM error.",
                    "raw_citations": []
                }
                
    return {
        "answer": "Failed to generate a valid answer (failed basic sanity checks after retries).",
        "raw_citations": []
    }
