import os
import json
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from src.workflow.runner import run_chronos_query
from src.api.schemas import QueryRequest, QueryResponse, HealthResponse, DocumentMetadata, IngestResponse
from src.ingestion.vector_store import ChromaVectorStore
from src.ingestion.pipeline import ingest_file, get_all_documents, DOCUMENTS_DIR

app = FastAPI(
    title="Project Chronos API",
    description="FastAPI web service wrapping the Project Chronos self-correcting temporal GraphRAG pipeline.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
    from src.utils.llm_client import validate_llm_connectivity
    validate_llm_connectivity()
    print("[*] Pre-loading embedding model and reranker...")

    try:
        from src.ingestion.embedder import Embedder
        _ = Embedder()
        from src.retrieval.reranker import Reranker
        _ = Reranker()
        print("[*] Models pre-loaded successfully.")
    except Exception as e:
        print(f"[WARNING] Model pre-loading encountered an error: {e}")

# In-memory session store for multi-turn chat memory
CHAT_SESSIONS: dict[str, list[dict]] = {}

@app.post("/api/query", response_model=QueryResponse)
async def query_pipeline(request: QueryRequest):
    """Executes a user query through the LangGraph self-correcting state machine."""
    try:
        session_id = request.session_id or "default"
        history = CHAT_SESSIONS.get(session_id, [])

        result = run_chronos_query(
            request.question,
            force_fallback=request.force_fallback,
            conversation_history=history
        )

        # Append turn to session memory
        if session_id not in CHAT_SESSIONS:
            CHAT_SESSIONS[session_id] = []
        CHAT_SESSIONS[session_id].append({"role": "user", "content": request.question})
        CHAT_SESSIONS[session_id].append({"role": "assistant", "content": result.get("answer", "")})

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

@app.delete("/api/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    """Clears conversation history for a given session ID."""
    if session_id in CHAT_SESSIONS:
        del CHAT_SESSIONS[session_id]
    return {"status": "success", "message": f"Session {session_id} memory cleared."}


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Returns database connectivity status and document ingest metrics."""
    from src.utils.llm_client import get_active_provider_info
    active_p_key, _ = get_active_provider_info()

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
        "chroma_document_count": chroma_count,
        "active_llm_provider": active_p_key
    }

@app.get("/api/providers")
async def list_providers():
    """Lists available LLM providers, active status, and configuration state."""
    from src.utils.llm_client import PROVIDERS_CONFIG, get_active_provider_info
    active_p_key, _ = get_active_provider_info()

    result = []
    for key, cfg in PROVIDERS_CONFIG.items():
        is_configured = True if key == "ollama" else bool(cfg["api_key"])
        result.append({
            "key": key,
            "name": cfg["name"],
            "is_active": (key == active_p_key),
            "configured": is_configured,
            "model": cfg["default_model"]
        })
    return result

@app.post("/api/providers/switch")
async def switch_provider(req: dict):
    """Switch active primary LLM provider at runtime."""
    provider = req.get("provider")
    from src.utils.llm_client import set_active_provider, PROVIDERS_CONFIG
    if not provider or provider not in PROVIDERS_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid provider '{provider}'.")
    
    success = set_active_provider(provider)
    return {"status": "success", "active_provider": provider}

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

@app.get("/api/analytics/confidence")
async def get_confidence_analytics():
    """Returns confidence score trends, averages, validation ratios, and retry distribution."""
    if not os.path.exists(LOG_FILE_PATH):
        return {
            "total_queries": 0,
            "average_confidence": 0,
            "validation_rate": 0,
            "average_retries": 0,
            "history": []
        }

    entries = []
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line.strip()))

        if not entries:
            return {
                "total_queries": 0,
                "average_confidence": 0,
                "validation_rate": 0,
                "average_retries": 0,
                "history": []
            }

        total = len(entries)
        avg_conf = sum(e.get("confidence_score", 0) for e in entries) / total
        valid_count = sum(1 for e in entries if e.get("is_valid", False))
        avg_retries = sum(e.get("retries", 0) for e in entries) / total

        return {
            "total_queries": total,
            "average_confidence": round(avg_conf, 1),
            "validation_rate": round((valid_count / total) * 100, 1),
            "average_retries": round(avg_retries, 2),
            "history": entries[-30:]  # Last 30 queries for trend chart
        }
    except Exception as e:
        print(f"[ERROR] Analytics aggregation failed: {e}")
        return {"error": str(e)}


@app.post("/api/ingest", response_model=IngestResponse)
async def upload_and_ingest_document(file: UploadFile = File(...)):
    """
    Uploads a document file (.pdf, .txt, .md), saves it to data/documents/,
    and executes vector embedding & knowledge graph extraction.
    """
    allowed_exts = {".pdf", ".txt", ".md", ".docx", ".xlsx", ".xls", ".csv"}
    filename = file.filename or "uploaded_doc.txt"
    ext = Path(filename).suffix.lower()

    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed formats: .pdf, .txt, .md, .docx, .xlsx, .xls, .csv"
        )

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = DOCUMENTS_DIR / filename

    try:
        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)
            
        ingest_result = ingest_file(str(target_path))
        return ingest_result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {str(e)}"
        )

@app.get("/api/documents", response_model=list[DocumentMetadata])
async def list_documents():
    """Returns status metadata cards for all uploaded/ingested documents."""
    try:
        return get_all_documents()
    except Exception as e:
        print(f"[ERROR] Failed to fetch documents list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph")
async def get_knowledge_graph(limit: int = 150):
    """Returns all entity nodes and relationships from Neo4j for knowledge graph visualization."""
    try:
        from src.graph.neo4j_client import Neo4jGraphStore
        store = Neo4jGraphStore()
        graph_data = store.get_full_graph(limit=limit)
        store.close()
        return graph_data
    except Exception as e:
        print(f"[WARNING] Graph data fetch failed: {e}")
        return {"nodes": [], "links": [], "error": str(e)}

@app.get("/api/timeline")
async def get_timeline_events():
    """Returns chronological temporal events extracted from Neo4j for the timeline visualizer."""
    try:
        from src.graph.neo4j_client import Neo4jGraphStore
        store = Neo4jGraphStore()
        events = store.get_temporal_events()
        store.close()
        return {"events": events}
    except Exception as e:
        print(f"[WARNING] Timeline fetch failed: {e}")
        return {"events": [], "error": str(e)}




