import time
from pathlib import Path
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import TextChunker
from src.ingestion.embedder import Embedder
from src.ingestion.vector_store import ChromaVectorStore

def run():
    print("====================================================")
    print("           Project Chronos Ingestion Pipeline       ")
    print("====================================================")
    
    # 1. Initialize Loader
    loader = DocumentLoader()
    docs_dir = Path(__file__).parent / "data" / "documents"
    print(f"[*] Loading documents from: {docs_dir.resolve()}")
    
    start_time = time.time()
    docs = loader.load_directory(str(docs_dir))
    load_time = time.time() - start_time
    print(f"[✓] Loaded {len(docs)} documents in {load_time:.2f} seconds.")
    if not docs:
        print("[!] No documents found to ingest. Exiting.")
        return

    # 2. Chunk Documents
    print("[*] Chunking documents...")
    chunker = TextChunker()
    chunks = chunker.split_documents(docs)
    print(f"[✓] Created {len(chunks)} chunks from {len(docs)} documents.")

    # 3. Embed Chunks
    print("[*] Initializing Embedder & embedding chunks...")
    embedder = Embedder()
    chunk_texts = [chunk.page_content for chunk in chunks]
    
    start_time = time.time()
    embeddings = embedder.embed_batch(chunk_texts)
    embed_time = time.time() - start_time
    print(f"[✓] Embedded {len(chunks)} chunks in {embed_time:.2f} seconds.")

    # 4. Store in Vector Store
    print("[*] Initializing Chroma Vector Store & storing chunks...")
    vector_store = ChromaVectorStore()
    
    start_time = time.time()
    vector_store.add_chunks(chunks, embeddings)
    store_time = time.time() - start_time
    print(f"[✓] Chunks added to ChromaDB in {store_time:.2f} seconds.")
    
    total_in_store = vector_store.count()
    print("====================================================")
    print(f"[SUCCESS] Ingestion completed successfully!")
    print(f" - Documents processed: {len(docs)}")
    print(f" - Chunks created:     {len(chunks)}")
    print(f" - Total chunks now:   {total_in_store}")
    print("====================================================")

if __name__ == "__main__":
    run()
