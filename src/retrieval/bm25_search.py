import re
from pathlib import Path
from rank_bm25 import BM25Okapi
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import TextChunker

class BM25Searcher:
    def __init__(self):
        loader = DocumentLoader()
        chunker = TextChunker()
        
        docs_dir = Path(__file__).parent.parent.parent / "data" / "documents"
        docs = loader.load_directory(str(docs_dir))
        self.chunks = chunker.split_documents(docs)
        
        tokenized_corpus = [self._tokenize(chunk.page_content) for chunk in self.chunks]
        
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r'\w+', text.lower())

    def search(self, query: str, top_k: int = 20) -> list[dict]:
        """Performs lexical search using BM25 and returns normalized candidates."""
        if not self.bm25 or not self.chunks:
            return []
            
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        candidates = []
        for idx, score in enumerate(scores):
            if score > 0:
                candidates.append({
                    "id": self.chunks[idx].metadata["chunk_id"],
                    "text": self.chunks[idx].page_content,
                    "metadata": self.chunks[idx].metadata,
                    "score": float(score),
                    "source": "bm25"
                })
                
        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        
        # Normalize BM25 scores to [0, 1] range
        if candidates:
            max_score = candidates[0]["score"]
            if max_score > 0:
                for c in candidates:
                    c["score"] = c["score"] / max_score
                    
        return candidates[:top_k]
