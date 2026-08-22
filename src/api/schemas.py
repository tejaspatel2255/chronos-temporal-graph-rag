from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class QueryRequest(BaseModel):
    question: str = Field(..., description="The user query to run through the self-correcting RAG pipeline.")
    force_fallback: bool = Field(False, description="If True, forces the pipeline to route to the web search fallback.")
    session_id: Optional[str] = Field(None, description="Session ID for multi-turn conversation memory.")

class Citation(BaseModel):
    source: str
    chunk_id: str

class ContextUsed(BaseModel):
    id: Optional[str] = None
    source: str
    text: str

class AttemptLog(BaseModel):
    retry_index: int
    query_used: str
    confidence: int
    reasoning: str

class QueryResponse(BaseModel):
    answer: str
    confidence_score: int
    is_valid: bool
    retries: int
    citations: List[Citation]
    context_used: List[ContextUsed]
    attempts_log: List[AttemptLog]
    suggested_questions: Optional[List[str]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    neo4j_connected: bool
    chroma_document_count: int
    active_llm_provider: str

class ProviderSwitchRequest(BaseModel):
    provider: str = Field(..., description="Target provider key (openrouter, groq, ollama, openai)")

class ProviderInfo(BaseModel):
    key: str
    name: str
    is_active: bool
    configured: bool
    model: str

class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    file_path: str
    file_size_bytes: int
    chunks_count: int
    created_at: str
    status: str
    tags: List[str] = Field(default_factory=list)

class TagUpdateRequest(BaseModel):
    filename: str
    tags: List[str]


class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    file_path: str
    file_size_bytes: int
    chunks_count: int
    created_at: str
    neo4j_status: str
    entities_created: int
    relationships_created: int
    status: str
