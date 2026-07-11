class HybridCombiner:
    def __init__(self, k: int = 60):
        self.k = k

    def combine(self, 
                vector_results: list[dict], 
                bm25_results: list[dict], 
                graph_results: list[dict], 
                structured_results: list[dict],
                router_analysis: dict) -> list[dict]:
        """Combines search results from multiple sources using Reciprocal Rank Fusion (RRF) with classification boosts."""
        
        classifications = [c.upper() for c in router_analysis.get("classification", [])]
        has_metrics = len(router_analysis.get("metrics", [])) > 0
        has_multiple_entities = len(router_analysis.get("entities", [])) > 1

        # Set default boosts
        boosts = {
            "vector": 1.0,
            "bm25": 1.0,
            "graph": 1.0,
            "structured": 1.0
        }

        # Apply boosts based on query routing classification
        if "FACTUAL" in classifications:
            boosts["vector"] += 0.5
            boosts["bm25"] += 0.3
            
        if "ANALYTICAL" in classifications or has_multiple_entities:
            boosts["graph"] += 0.8
            
        if has_metrics:
            boosts["structured"] += 1.0

        rrf_scores = {}
        candidate_map = {}

        def process_system_results(results: list[dict], source: str):
            sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
            for rank, item in enumerate(sorted_results):
                key = item.get("id") or item.get("text")
                
                if key not in candidate_map:
                    candidate_map[key] = {
                        "id": item["id"],
                        "text": item["text"],
                        "metadata": item["metadata"],
                        "source": item["source"],
                        "original_scores": {source: item["score"]}
                    }
                else:
                    candidate_map[key]["original_scores"][source] = item["score"]
                    if source in ["structured", "graph"]:
                        candidate_map[key]["source"] = source
                        candidate_map[key]["metadata"] = item["metadata"]

                rank_score = boosts[source] / (self.k + rank + 1)
                rrf_scores[key] = rrf_scores.get(key, 0.0) + rank_score

        # Process all sources
        process_system_results(vector_results, "vector")
        process_system_results(bm25_results, "bm25")
        process_system_results(graph_results, "graph")
        process_system_results(structured_results, "structured")

        combined_candidates = []
        for key, rrf_score in rrf_scores.items():
            candidate = candidate_map[key].copy()
            candidate["score"] = rrf_score
            combined_candidates.append(candidate)

        combined_candidates = sorted(combined_candidates, key=lambda x: x["score"], reverse=True)
        return combined_candidates
