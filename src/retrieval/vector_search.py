from src.ingestion.embedder import Embedder
from src.ingestion.vector_store import ChromaVectorStore

class VectorSearcher:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = ChromaVectorStore()

    def search(self, query: str, top_k: int = 20) -> list[dict]:
        """Embeds the query and searches ChromaDB, returning a list of candidates with scores."""
        query_embeddings = self.embedder.embed_batch([query])
        if not query_embeddings:
            return []
            
        results = self.vector_store.query(query_embeddings, n_results=top_k)
        
        candidates = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            ids = results["ids"][0]
            
            for idx in range(len(docs)):
                # Convert cosine distance to similarity score
                similarity_score = 1.0 - distances[idx]
                
                candidates.append({
                    "id": ids[idx],
                    "text": docs[idx],
                    "metadata": metadatas[idx],
                    "score": similarity_score,
                    "source": "vector"
                })
        return candidates
