from src.workflow.graph_builder import build_chronos_graph
from src.workflow.output_formatter import format_chronos_output

# Instantiate graph once during import to avoid reloading dependencies
chronos_graph = build_chronos_graph()

def run_chronos_query(question: str, force_fallback: bool = False) -> dict:
    """Executes the query through the compiled LangGraph workflow state machine."""
    initial_state = {
        "question": question,
        "original_query": question,
        "query_analysis": {},
        "retrieved_docs": [],
        "graph_data": [],
        "structured_data": [],
        "combined_candidates": [],
        "reranked_candidates": [],
        "draft_answer": "",
        "validation_result": {},
        "is_valid": False,
        "retry_count": 0,
        "confidence_score": 0,
        "citations": [],
        "context_used": [],
        "attempts_log": [],
        "web_fallback_run": False,
        "force_fallback": force_fallback
    }
    
    try:
        final_state = chronos_graph.invoke(initial_state)
        return format_chronos_output(final_state)
    except Exception as e:
        print(f"[CRITICAL] LangGraph execution error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "answer": f"System error during query execution: {str(e)}",
            "confidence_score": 0,
            "is_valid": False,
            "retries": 0,
            "citations": [],
            "context_used": [],
            "attempts_log": [
                {
                    "retry_index": 0,
                    "query_used": question,
                    "confidence": 0,
                    "reasoning": f"Critical Failure: {str(e)}"
                }
            ]
        }
