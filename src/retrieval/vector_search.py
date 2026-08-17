from typing import List, Dict, Any
from src.ingestion.embedder import Embedder
from src.ingestion.vector_store import ChromaVectorStore

class VectorSearcher:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = ChromaVectorStore()

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Embeds the query and searches ChromaDB, returning a list of candidates with scores."""
        query_embeddings = self.embedder.embed_batch([query])
        if not query_embeddings:
            return []
            
        results = self.vector_store.query(query_embeddings, n_results=top_k)
        
        candidates = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if ("metadatas" in results and results["metadatas"]) else []
            distances = results["distances"][0] if ("distances" in results and results["distances"]) else [0.0] * len(docs)
            ids = results["ids"][0] if ("ids" in results and results["ids"]) else [f"vec_{i}" for i in range(len(docs))]
            
            for idx in range(len(docs)):
                # Convert cosine distance to similarity score
                dist = distances[idx] if idx < len(distances) else 0.0
                similarity_score = 1.0 - float(dist)
                
                meta = metadatas[idx] if (idx < len(metadatas) and isinstance(metadatas[idx], dict)) else {}
                chunk_id = ids[idx] if idx < len(ids) else f"vec_{idx}"

                candidates.append({
                    "id": chunk_id,
                    "text": docs[idx],
                    "metadata": meta,
                    "score": similarity_score,
                    "source": "vector"
                })
        return candidates
