import os
import hashlib
from typing import Optional, List, Dict, Any
import chromadb
from langchain_core.documents import Document
from config.settings import settings

class ChromaVectorStore:
    def __init__(self, persist_dir: Optional[str] = None) -> None:
        if persist_dir is None:
            persist_dir = settings.CHROMA_PERSIST_DIR
            
        os.makedirs(persist_dir, exist_ok=True)

        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Create or get collection with cosine similarity
        self.collection = self.client.get_or_create_collection(
            name="chronos_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Document], embeddings: List[List[float]]) -> None:
        """Stores chunk texts, metadata, and embeddings in ChromaDB using chunk_id as the ID."""
        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise ValueError("The number of chunks and embeddings must match.")

        ids: List[str] = []
        for chunk in chunks:
            c_id = chunk.metadata.get("chunk_id")
            if not c_id:
                c_id = hashlib.md5(chunk.page_content.encode("utf-8")).hexdigest()
            ids.append(str(c_id))
        
        # Sanitize metadata dicts so ChromaDB receives valid primitive types (str, int, float, bool)
        sanitized_metadatas: List[Dict[str, Any]] = []
        for chunk in chunks:
            clean_meta: Dict[str, Any] = {}
            for k, v in chunk.metadata.items():
                if v is None:
                    continue
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            sanitized_metadatas.append(clean_meta)

        documents: List[str] = [chunk.page_content for chunk in chunks]

        # Chroma's upsert handles list of strings, embeddings list, dicts metadata
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=sanitized_metadatas,
            documents=documents
        )

    def count(self) -> int:
        """Returns the total number of chunks in the collection."""
        return self.collection.count()

    def peek(self, n: int = 5) -> Dict[str, Any]:
        """Returns a preview of the first n items in the collection."""
        total = self.count()
        if total == 0:
            return {"ids": [], "embeddings": [], "metadatas": [], "documents": []}
        return dict(self.collection.peek(limit=min(n, total)))

    def query(self, query_embeddings: List[List[float]], n_results: int = 5) -> Dict[str, Any]:
        """Queries the vector store collection using embeddings."""
        total = self.count()
        if total == 0:
            return {"ids": [[]], "distances": [[]], "metadatas": [[]], "documents": [[]]}
        
        safe_n = max(1, min(n_results, total))
        return dict(self.collection.query(
            query_embeddings=query_embeddings,
            n_results=safe_n
        ))
