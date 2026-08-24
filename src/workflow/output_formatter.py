from src.generation.evaluator import evaluator

def format_chronos_output(state: dict) -> dict:
    """Formats the final state dictionary into a clean structured JSON schema with quantitative RAGAS metrics."""
    answer = state.get("draft_answer", "")
    question = state.get("question", "")
    contexts = [c.get("text", "") for c in state.get("context_used", []) if c.get("text")]

    # Compute quantitative RAGAS evaluation metrics
    ragas_metrics = evaluator.evaluate_response(question, answer, contexts)

    return {
        "answer": answer,
        "confidence_score": state.get("confidence_score", 0),
        "is_valid": state.get("is_valid", False),
        "retries": state.get("retry_count", 0),
        "citations": state.get("citations", []),
        "context_used": state.get("context_used", []),
        "attempts_log": state.get("attempts_log", []),
        "suggested_questions": state.get("suggested_questions", []),
        "ragas_eval": ragas_metrics
    }

