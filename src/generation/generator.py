import re
from src.generation.prompts import SYSTEM_PROMPT, build_generation_prompt

def generate_draft(query: str, context_chunks: list[dict], llm_client, conversation_history: list[dict] = None) -> dict:
    """Generates a draft answer using the LLM and extracts inline source citations."""
    prompt = build_generation_prompt(query, context_chunks, conversation_history=conversation_history)
    
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

def generate_suggested_questions(query: str, answer: str, llm_client) -> list[str]:
    """Generates 3 auto-suggested follow-up questions using the LLM."""
    import json
    from src.generation.prompts import SUGGESTED_QUESTIONS_PROMPT, build_suggestions_prompt

    prompt = build_suggestions_prompt(query, answer)
    try:
        response = llm_client.completion(
            prompt=prompt,
            system_prompt=SUGGESTED_QUESTIONS_PROMPT,
            temperature=0.4
        )
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        questions = json.loads(cleaned)
        if isinstance(questions, list) and len(questions) > 0:
            return [str(q).strip() for q in questions[:3]]
    except Exception as e:
        print(f"[WARNING] Failed to generate suggested follow-up questions: {e}")

    # Fallback contextual questions if generation fails
    return [
        f"What are the temporal trends related to {query[:30]}...?",
        f"How does this impact overall strategic milestones?",
        f"Can you summarize key risk factors associated with this topic?"
    ]

