from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        # Cache CrossEncoder locally on CPU
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-2-v2", device="cpu")

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """Reranks candidates using the CrossEncoder model."""
        if not candidates:
            return []
            
        pairs = [(query, cand.get("text", "")) for cand in candidates]
        scores = self.model.predict(pairs)
        
        reranked_candidates = []
        for idx, score in enumerate(scores):
            cand = candidates[idx].copy()
            cand["rerank_score"] = float(score)
            cand["score"] = float(score)
            reranked_candidates.append(cand)
            
        reranked_candidates = sorted(reranked_candidates, key=lambda x: x.get("score", 0.0), reverse=True)
        return reranked_candidates[:top_n]
