import re
from src.generation.prompts import SYSTEM_PROMPT, build_generation_prompt

def generate_draft(query: str, context_chunks: list[dict], llm_client) -> dict:
    """Generates a draft answer using OpenRouter and extracts inline source citations."""
    prompt = build_generation_prompt(query, context_chunks)
    
    try:
        response = llm_client.completion(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3
        )
        
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
        print(f"[ERROR] Answer generation failed: {e}")
        return {
            "answer": "Failed to generate an answer due to an internal LLM error.",
            "raw_citations": []
        }
