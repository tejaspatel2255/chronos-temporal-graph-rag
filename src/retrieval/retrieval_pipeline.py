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

class RetrievalPipeline:
    def __init__(self):
        self.llm_client = LLMClient()
        self.vector_searcher = VectorSearcher()
        self.bm25_searcher = BM25Searcher()
        self.graph_searcher = GraphSearcher()
        self.structured_searcher = StructuredSearcher()
        self.combiner = HybridCombiner()
        self.reranker = Reranker()

    def run(self, query: str) -> dict:
        """Runs the complete retrieval pipeline: classify -> parallel search -> combine -> weight -> rerank."""
        # 1. Classify query
        print(f"[*] Analyzing query: '{query}'")
        analysis = classify_query(query, self.llm_client)
        print(f"[✓] Classifications: {analysis.get('classification')}")
        print(f" - Entities: {analysis.get('entities')}")
        print(f" - Timeframe: '{analysis.get('timeframe')}'")
        print(f" - Metrics: {analysis.get('metrics')}")
        
        entities = analysis.get("entities", [])
        timeframe = analysis.get("timeframe", "")
        metrics = analysis.get("metrics", [])
        classifications = analysis.get("classification", [])
        
        # 2. Run searches concurrently
        print("[*] Launching parallel multi-source searches...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_vector = executor.submit(self.vector_searcher.search, query, top_k=20)
            future_bm25 = executor.submit(self.bm25_searcher.search, query, top_k=20)
            future_graph = executor.submit(self.graph_searcher.search, entities)
            future_struct = executor.submit(self.structured_searcher.search, query, entities, timeframe, metrics)
            
            vector_res = future_vector.result()
            bm25_res = future_bm25.result()
            graph_res = future_graph.result()
            struct_res = future_struct.result()
            
        print(f"[✓] Retrieved candidates: Vector: {len(vector_res)} | BM25: {len(bm25_res)} | Graph: {len(graph_res)} | Structured: {len(struct_res)}")

        # 3. Combine results using RRF
        combined = self.combiner.combine(
            vector_results=vector_res,
            bm25_results=bm25_res,
            graph_results=graph_res,
            structured_results=struct_res,
            router_analysis=analysis
        )
        print(f"[✓] Combined {len(combined)} unique candidates using RRF.")

        # 4. Apply temporal weighting
        weighted = apply_temporal_weighting(
            candidates=combined,
            timeframe=timeframe,
            classifications=classifications
        )

        # 5. Rerank top 25 candidates using CrossEncoder
        candidates_to_rerank = weighted[:25]
        print(f"[*] Reranking top {len(candidates_to_rerank)} candidates...")
        final_top_5 = self.reranker.rerank(query, candidates_to_rerank, top_n=5)
        print("[✓] Rerank complete.")

        return {
            "query": query,
            "analysis": analysis,
            "results": final_top_5
        }
