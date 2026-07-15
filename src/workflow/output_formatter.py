def format_chronos_output(state: dict) -> dict:
    """Formats the final state dictionary into a clean structured JSON schema."""
    return {
        "answer": state.get("draft_answer", ""),
        "confidence_score": state.get("confidence_score", 0),
        "is_valid": state.get("is_valid", False),
        "retries": state.get("retry_count", 0),
        "citations": state.get("citations", []),
        "context_used": state.get("context_used", []),
        "attempts_log": state.get("attempts_log", [])
    }
