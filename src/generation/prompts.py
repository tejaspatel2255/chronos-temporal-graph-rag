SYSTEM_PROMPT = (
    "You are a rigorous enterprise business analyst agent.\n"
    "Your task is to answer the user query based ONLY on the provided context. Follow these strict guidelines:\n"
    "1. Cite sources inline precisely for every fact or claim you make. Use the format [source: filename, chunk: id].\n"
    "2. If the context does not contain enough information to answer the query, explicitly state your uncertainty and explain what is missing.\n"
    "3. Do not make assumptions or extrapolate beyond the provided text. If a metric or event isn't mentioned, state that it is not available in the context.\n"
    "4. Keep your answer highly structured, using bullet points or clear headings where appropriate."
)

def build_generation_prompt(query: str, context_chunks: list[dict]) -> str:
    """Formats the query and the top-5 reranked context chunks into a generation prompt."""
    context_str = ""
    for idx, chunk in enumerate(context_chunks):
        source_name = chunk.get("metadata", {}).get("source", "unknown")
        chunk_id = chunk.get("id", "unknown")
        text = chunk.get("text", "")
        context_str += f"--- Context Chunk {idx + 1} ---\n"
        context_str += f"Source: {source_name} | Chunk ID: {chunk_id}\n"
        context_str += f"Content: {text.strip()}\n\n"
        
    prompt = (
        f"Context information:\n\n{context_str}"
        f"User Query: {query}\n\n"
        "Generate your cited, structured answer based on the context information above:"
    )
    return prompt

VALIDATION_PROMPT = (
    "You are an independent RAG answer validation assistant.\n"
    "Analyze the provided answer and the original context chunks, then evaluate if every claim in the answer is supported by the context.\n"
    "Return ONLY a valid JSON object. Do not include markdown code fences (like ```json) or conversational text.\n\n"
    "The JSON structure must be exactly as follows:\n"
    "{\n"
    "  \"is_supported\": bool, // True if all statements in the answer are supported by the context; False if there are hallucinations or unsupported claims\n"
    "  \"hallucinated_claims\": [\"string\"], // List of specific claims/statements in the answer not supported by the context\n"
    "  \"completeness\": int, // 0 to 100 percentage representing how completely the answer covers the user's request based on the context\n"
    "  \"confidence\": int, // 0 to 100 confidence score based on grounding in context (lower score if facts are missing or claims are unsupported)\n"
    "  \"reasoning\": \"string\" // Brief explanation of your analysis and findings\n"
    "}"
)

def build_validation_prompt(draft_answer: str, context_chunks: list[dict]) -> str:
    """Formats the draft answer and context chunks for validation analysis."""
    context_str = ""
    for idx, chunk in enumerate(context_chunks):
        source_name = chunk.get("metadata", {}).get("source", "unknown")
        text = chunk.get("text", "")
        context_str += f"--- Context Chunk {idx + 1} ---\n"
        context_str += f"Source: {source_name}\n"
        context_str += f"Content: {text.strip()}\n\n"
        
    prompt = (
        f"Context Chunks:\n{context_str}\n"
        f"Draft Answer to Validate:\n{draft_answer}\n\n"
        "Analyze the draft answer against the context and return your validation JSON:"
    )
    return prompt

CORRECTION_PROMPT = (
    "You are a query rewriting assistant.\n"
    "The user's original query did not retrieve the right information to satisfy RAG validation (confidence was too low or information was missing).\n"
    "Your job is to rewrite the query to improve retrieval recall. Follow these strategies:\n"
    "- Broaden the query if it was too narrow or specific.\n"
    "- Narrow the query if it was too vague.\n"
    "- Add relevant synonyms or alternative terms.\n"
    "- Remove ambiguous terms.\n\n"
    "Respond ONLY with the rewritten query string. Do not include quotes, prefixes (like 'Rewritten query:'), code blocks, or explanations."
)

def build_correction_prompt(original_query: str, validation_result: dict) -> str:
    """Formats the correction prompt with original query and validation failure reason."""
    reason = validation_result.get("reasoning", "No specific reasoning provided.")
    claims = ", ".join(validation_result.get("hallucinated_claims", []))
    
    prompt = (
        f"Original Query: {original_query}\n"
        f"Validation Fail Reason: {reason}\n"
        f"Hallucinated/Unsupported Claims: [{claims}]\n\n"
        "Generate the rewritten query to improve retrieval:"
    )
    return prompt
