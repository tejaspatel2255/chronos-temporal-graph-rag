import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.workflow.runner import run_chronos_query
from src.api.schemas import QueryRequest, QueryResponse, HealthResponse
from src.ingestion.vector_store import ChromaVectorStore

app = FastAPI(
    title="Project Chronos API",
    description="FastAPI web service wrapping the Project Chronos self-correcting temporal GraphRAG pipeline.",
    version="1.0.0"
)

# CORS Configuration
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_FILE_PATH = "data/logs/query_log.jsonl"

def log_query_to_file(question: str, response: dict):
    """Appends a query and its metadata as a JSON line to data/logs/query_log.jsonl."""
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "confidence_score": response.get("confidence_score", 0),
        "is_valid": response.get("is_valid", False),
        "retries": response.get("retries", 0)
    }
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

@app.on_event("startup")
async def startup_event():
    """Startup event handler to pre-load ML models and prevent per-request reload latency."""
    print("[*] Starting FastAPI Web Server...")
    print("[*] Pre-loading embedding model and reranker...")
    try:
        from src.ingestion.embedder import Embedder
        _ = Embedder()
        from src.retrieval.reranker import Reranker
        _ = Reranker()
        print("[*] Models pre-loaded successfully.")
    except Exception as e:
        print(f"[WARNING] Model pre-loading encountered an error: {e}")

@app.post("/api/query", response_model=QueryResponse)
async def query_pipeline(request: QueryRequest):
    """Executes a user query through the LangGraph self-correcting state machine."""
    try:
        result = run_chronos_query(request.question, force_fallback=request.force_fallback)
        
        # Log execution outcome to local logs
        log_query_to_file(request.question, result)
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error occurred during query execution: {str(e)}"
        )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Returns database connectivity status and document ingest metrics."""
    neo4j_connected = False
    try:
        from src.graph.neo4j_client import Neo4jGraphStore
        store = Neo4jGraphStore()
        neo4j_connected = True
        store.close()
    except Exception as e:
        print(f"[WARNING] Health check Neo4j connectivity check failed: {e}")
        
    chroma_count = 0
    try:
        vector_store = ChromaVectorStore()
        chroma_count = vector_store.count()
    except Exception as e:
        print(f"[WARNING] Health check Chroma document count check failed: {e}")
        
    return {
        "status": "healthy",
        "neo4j_connected": neo4j_connected,
        "chroma_document_count": chroma_count
    }

@app.get("/api/history")
async def get_query_history(limit: int = 10):
    """Returns the last N logged query events."""
    if not os.path.exists(LOG_FILE_PATH):
        return []
        
    entries = []
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line.strip()))
        return entries[-limit:]
    except Exception as e:
        print(f"[ERROR] Failed to read query history: {e}")
        return []
