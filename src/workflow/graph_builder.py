from langgraph.graph import StateGraph, END
from src.workflow.state import ChronosState
from src.workflow.nodes import (
    classify_query_node,
    retrieve_node,
    rerank_node,
    generate_node,
    validate_node,
    correct_node,
    web_fallback_node
)

def should_continue(state: ChronosState) -> str:
    """Decides if the state machine should stop, attempt query correction, or run web search fallback."""
    if state.get("is_valid", False):
        return "end"
        
    # If not valid, check retries
    if state.get("retry_count", 0) < 2:
        return "correct"
        
    # If retries exhausted, check if we did web search fallback yet
    if not state.get("web_fallback_run", False):
        return "web_fallback"
        
    return "end"

def build_chronos_graph():
    """Builds and compiles the self-correcting RAG state machine."""
    workflow = StateGraph(ChronosState)
    
    # Register Nodes
    workflow.add_node("classify", classify_query_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("correct", correct_node)
    workflow.add_node("web_fallback", web_fallback_node)
    
    # Establish Connections
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "generate")
    workflow.add_edge("generate", "validate")
    
    # Conditional Router Edge
    workflow.add_conditional_edges(
        "validate",
        should_continue,
        {
            "end": END,
            "correct": "correct",
            "web_fallback": "web_fallback"
        }
    )
    
    # Loop back to retrieval from correction node
    workflow.add_edge("correct", "retrieve")
    
    # Web fallback routes directly to generator node for rewriting with web context
    workflow.add_edge("web_fallback", "generate")
    
    return workflow.compile()
