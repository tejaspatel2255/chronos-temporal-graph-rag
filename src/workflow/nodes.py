from concurrent.futures import ThreadPoolExecutor
from src.utils.llm_client import LLMClient
from src.retrieval.query_router import classify_query
from src.retrieval.vector_search import VectorSearcher
from src.retrieval.bm25_search import BM25Searcher
from src.retrieval.graph_search import GraphSearcher
from src.retrieval.structured_search import StructuredSearcher
from src.retrieval.hybrid_combiner import HybridCombiner
from src.retrieval.temporal_weighting import apply_temporal_weighting
from src.retrieval.reranker import Reranker
from src.generation.generator import generate_draft
from src.generation.validator import validate_answer
from src.generation.corrector import rewrite_query
from src.workflow.state import ChronosState
from src.retrieval.web_fallback import WebSearchFallback

# Initialize retrieval/generation components once to reuse across steps
llm_client = LLMClient()
vector_searcher = VectorSearcher()
bm25_searcher = BM25Searcher()
graph_searcher = GraphSearcher()
structured_searcher = StructuredSearcher()
combiner = HybridCombiner()
reranker = Reranker()
web_searcher = WebSearchFallback()

def classify_query_node(state: ChronosState) -> dict:
    """Classifies query and extracts entities, timeframe, metrics, and paraphrases."""
    query = state["question"]
    print(f"[*] [LangGraph Node: Classify] Analyzing query: '{query}'")
    analysis = classify_query(query, llm_client)
    return {
        "query_analysis": analysis
    }

def retrieve_node(state: ChronosState) -> dict:
    """Runs parallel searches across all retrieval sources and combines results using RRF."""
    query = state["question"]
    analysis = state["query_analysis"]
    
    entities = analysis.get("entities", [])
    timeframe = analysis.get("timeframe", "")
    metrics = analysis.get("metrics", [])
    classifications = analysis.get("classification", [])
    
    print("[*] [LangGraph Node: Retrieve] Querying dense, lexical, structured, and graph databases concurrently...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_vector = executor.submit(vector_searcher.search, query, top_k=20)
        future_bm25 = executor.submit(bm25_searcher.search, query, top_k=20)
        future_graph = executor.submit(graph_searcher.search, entities)
        future_struct = executor.submit(structured_searcher.search, query, entities, timeframe, metrics)
        
        vector_res = future_vector.result()
        bm25_res = future_bm25.result()
        graph_res = future_graph.result()
        struct_res = future_struct.result()
        
    print(f" - Candidate counts: Vector: {len(vector_res)} | BM25: {len(bm25_res)} | Graph: {len(graph_res)} | Structured: {len(struct_res)}")
    
    # Reciprocal Rank Fusion
    combined = combiner.combine(
        vector_results=vector_res,
        bm25_results=bm25_res,
        graph_results=graph_res,
        structured_results=struct_res,
        router_analysis=analysis
    )
    
    # Adjust scores based on exact timeframe match and recency decay
    weighted = apply_temporal_weighting(
        candidates=combined,
        timeframe=timeframe,
        classifications=classifications
    )
    
    return {
        "retrieved_docs": vector_res + bm25_res,
        "graph_data": graph_res,
        "structured_data": struct_res,
        "combined_candidates": weighted
    }

def rerank_node(state: ChronosState) -> dict:
    """Reranks candidates using local Cross-Encoder model and selects top 5."""
    query = state["question"]
    candidates = state["combined_candidates"]
    
    candidates_to_rerank = candidates[:25]
    print(f"[*] [LangGraph Node: Rerank] Reranking top {len(candidates_to_rerank)} candidates...")
    reranked = reranker.rerank(query, candidates_to_rerank, top_n=5)
    return {
        "reranked_candidates": reranked
    }

def generate_node(state: ChronosState) -> dict:
    """Generates drafted answer with inline citations using context chunks."""
    query = state["question"]
    context = state["reranked_candidates"]
    print("[*] [LangGraph Node: Generate] Drafting response using context...")
    draft = generate_draft(query, context, llm_client)
    return {
        "draft_answer": draft["answer"],
        "citations": draft["raw_citations"],
        "context_used": [
            {
                "id": c.get("id"),
                "source": c.get("metadata", {}).get("source", "unknown"),
                "text": c.get("text")
            }
            for c in context
        ]
    }

def validate_node(state: ChronosState) -> dict:
    """Evaluates the draft answer against original retrieved context."""
    draft = state["draft_answer"]
    context = state["reranked_candidates"]
    print("[*] [LangGraph Node: Validate] Verifying claims against context...")
    validation = validate_answer(draft, context, llm_client)
    
    confidence = validation.get("confidence", 0)
    is_valid = confidence >= 70
    
    # Force fallback override for testing purposes
    if state.get("force_fallback", False) and not state.get("web_fallback_run", False):
        print("[!] force_fallback is active: Overriding validation to trigger correction/fallback path.")
        confidence = 0
        is_valid = False
        
    # Log attempt
    log_entry = {
        "retry_index": state.get("retry_count", 0),
        "query_used": state["question"],
        "confidence": confidence,
        "reasoning": validation.get("reasoning", "") if not state.get("force_fallback", False) else "Forced validation failure for testing fallback."
    }
    current_logs = list(state.get("attempts_log", []))
    current_logs.append(log_entry)
    
    print(f" - Results: Confidence={confidence}% | Is Valid={is_valid}")
    
    return {
        "validation_result": validation,
        "is_valid": is_valid,
        "confidence_score": confidence,
        "attempts_log": current_logs
    }

def correct_node(state: ChronosState) -> dict:
    """Rewrites query using failure reasoning to improve retrieval recall."""
    original_query = state["question"]
    validation = state["validation_result"]
    print("[*] [LangGraph Node: Correct] Confidence score low. Rewriting query...")
    new_query = rewrite_query(original_query, validation, llm_client)
    print(f" - New Query: '{new_query}'")
    return {
        "question": new_query,
        "retry_count": state.get("retry_count", 0) + 1
    }

def web_fallback_node(state: ChronosState) -> dict:
    """Triggered as a fallback path when local databases fail to produce high-confidence answers."""
    query = state["question"]
    print(f"[*] [LangGraph Node: Web Fallback] Initiating web search fallback for: '{query}'")
    web_results = web_searcher.search(query)
    return {
        "reranked_candidates": web_results,
        "web_fallback_run": True,
        "is_valid": False
    }
