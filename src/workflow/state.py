from typing import TypedDict, List, Dict, Any

class ChronosState(TypedDict):
    question: str
    original_query: str
    query_analysis: Dict[str, Any]
    retrieved_docs: List[Dict[str, Any]]
    graph_data: List[Dict[str, Any]]
    structured_data: List[Dict[str, Any]]
    combined_candidates: List[Dict[str, Any]]
    reranked_candidates: List[Dict[str, Any]]
    draft_answer: str
    validation_result: Dict[str, Any]
    is_valid: bool
    retry_count: int
    confidence_score: int
    citations: List[Dict[str, Any]]
    context_used: List[Dict[str, Any]]
    attempts_log: List[Dict[str, Any]]
    web_fallback_run: bool
    force_fallback: bool
