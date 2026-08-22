import re
from pathlib import Path
from rank_bm25 import BM25Okapi
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import TextChunker

from typing import List, Dict, Any

class BM25Searcher:
    def __init__(self):
        self.chunks = []
        self.bm25 = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
            
        try:
            loader = DocumentLoader()
            chunker = TextChunker()
            
            docs_dir = Path(__file__).parent.parent.parent / "data" / "documents"
            if docs_dir.exists():
                docs = loader.load_directory(str(docs_dir))
                self.chunks = chunker.split_documents(docs)
                
                tokenized_corpus = [self._tokenize(chunk.page_content) for chunk in self.chunks]
                if tokenized_corpus:
                    self.bm25 = BM25Okapi(tokenized_corpus)
        except Exception as e:
            print(f"[WARNING] Failed to initialize BM25 searcher: {e}")
            self.bm25 = None
            self.chunks = []
            
        self._initialized = True

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r'\w+', text.lower())

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Performs lexical search using BM25 and returns normalized candidates."""
        self._ensure_initialized()
        
        if not self.bm25 or not self.chunks:
            return []
            
        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []
            
        scores = self.bm25.get_scores(tokenized_query)
        
        candidates = []
        for idx, score in enumerate(scores):
            if score > 0:
                chunk = self.chunks[idx]
                chunk_id = chunk.metadata.get("chunk_id", f"bm25_chunk_{idx}")
                candidates.append({
                    "id": chunk_id,
                    "text": chunk.page_content,
                    "metadata": chunk.metadata,
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

