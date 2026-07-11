import chromadb
from langchain_core.documents import Document
from config.settings import settings

class ChromaVectorStore:
    def __init__(self, persist_dir: str = None):
        if persist_dir is None:
            persist_dir = settings.CHROMA_PERSIST_DIR
            
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Create or get collection with cosine similarity
        self.collection = self.client.get_or_create_collection(
            name="chronos_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: list[Document], embeddings: list[list[float]]):
        """Stores chunk texts, metadata, and embeddings in ChromaDB using chunk_id as the ID."""
        if not chunks:
            return

        if len(chunks) != len(embeddings):
            raise ValueError("The number of chunks and embeddings must match.")

        ids = [chunk.metadata["chunk_id"] for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        documents = [chunk.page_content for chunk in chunks]

        # Chroma's add handles list of strings, embeddings list, dicts metadata
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def count(self) -> int:
        """Returns the total number of chunks in the collection."""
        return self.collection.count()

    def peek(self, n: int = 5) -> dict:
        """Returns a preview of the first n items in the collection."""
        return self.collection.peek(limit=n)

    def query(self, query_embeddings: list[list[float]], n_results: int = 5) -> dict:
        """Queries the vector store collection using embeddings."""
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )
