from src.ingestion.embedder import Embedder
from src.ingestion.vector_store import ChromaVectorStore

def run():
    print("====================================================")
    print("       Project Chronos Retrieval Verification        ")
    print("====================================================")
    
    # Initialize components
    embedder = Embedder()
    vector_store = ChromaVectorStore()
    
    # Check count
    total_count = vector_store.count()
    print(f"[*] Current number of chunks in ChromaDB: {total_count}")
    if total_count == 0:
        print("[!] No chunks found in the database. Please run run_ingestion.py first.")
        return

    # Sample query
    query_text = "What competitor did the company mention in Q2 2024?"
    print(f"[*] Querying ChromaDB for: '{query_text}'")
    
    # Embed the query
    query_embedding = embedder.embed_batch([query_text])[0]
    
    # Query vector store
    results = vector_store.collection.query(
        query_embeddings=[query_embedding],
        n_results=1
    )
    
    # Print results
    print("\n[✓] Retrieval Top Result:")
    if results and results["documents"] and results["documents"][0]:
        document_text = results["documents"][0][0]
        metadata = results["metadatas"][0][0]
        distance = results["distances"][0][0] if "distances" in results else "N/A"
        
        print(f"--- Text ---")
        print(document_text)
        print(f"------------")
        print(f"Distance (Cosine): {distance}")
        print(f"Metadata: {metadata}")
    else:
        print("[!] No results returned.")
    print("====================================================")

if __name__ == "__main__":
    run()
