from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import TextChunker
from src.ingestion.embedder import Embedder
from src.ingestion.vector_store import ChromaVectorStore
from src.graph.neo4j_client import Neo4jGraphStore
from src.graph.entity_extractor import extract_entities, extract_relationships
from src.utils.llm_client import LLMClient

DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "data" / "documents"

def _safe_isoformat(timestamp: float) -> str:
    try:
        return datetime.fromtimestamp(timestamp).isoformat()
    except Exception:
        return datetime.utcnow().isoformat()

def ingest_file(file_path: str, progress_callback=None) -> Dict[str, Any]:
    """
    Ingests a single file end-to-end into ChromaDB vector store
    and extracts graph entities into Neo4j if reachable.
    Optionally reports stage updates to progress_callback.
    """
    def _notify(stage: str, progress: int, details: str = ""):
        if progress_callback:
            try:
                progress_callback(stage, progress, details)
            except Exception:
                pass

    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 1. Load document
    _notify("loading", 15, "Reading document structure and content...")
    loader = DocumentLoader()
    doc = loader.load_file(str(path))

    # 2. Chunk document
    _notify("chunking", 35, "Splitting document into semantic chunks...")
    chunker = TextChunker()
    chunks = chunker.split_documents([doc])

    # 3. Embed chunks
    _notify("embedding", 55, f"Generating vector embeddings for {len(chunks)} chunks...")
    embedder = Embedder()
    chunk_texts = [c.page_content for c in chunks]
    embeddings = embedder.embed_batch(chunk_texts)

    # 4. Store in Chroma Vector Store
    _notify("indexing", 75, "Storing chunks and embeddings into ChromaDB index...")
    vector_store = ChromaVectorStore()
    vector_store.add_chunks(chunks, embeddings)

    # 5. Populate Neo4j Graph Entities
    _notify("extracting_graph", 90, "Extracting entity nodes and temporal relationships into Neo4j...")

    entities_created = 0
    relationships_created = 0
    neo4j_status = "offline"

    try:
        llm_client = LLMClient()
        with Neo4jGraphStore() as graph_store:
            doc_name = doc.metadata.get("source", path.name)
            doc_id = doc.metadata.get("doc_id", "unknown")

            # Create document node
            graph_store.create_entity_node(
                name=doc_name,
                type="Document",
                properties={
                    "doc_id": doc_id,
                    "created_at": doc.metadata.get("created_at", ""),
                    "modified_at": doc.metadata.get("modified_at", "")
                }
            )

            for chunk in chunks:
                text = chunk.page_content
                entities = extract_entities(text, llm_client)

                flat_entities = []
                for entity_type, entity_list in entities.items():
                    if not isinstance(entity_list, list):
                        continue
                    key = str(entity_type).lower().strip()
                    std_type = "Person"
                    if key in ("companies", "company"):
                        std_type = "Company"
                    elif key in ("products", "product"):
                        std_type = "Product"
                    elif key in ("events", "event"):
                        std_type = "Event"
                    elif key in ("metrics", "metric"):
                        std_type = "Metric"
                    elif key in ("people", "person"):
                        std_type = "Person"

                    for ent in entity_list:
                        if isinstance(ent, dict):
                            ent_name = ent.get("name")
                            if ent_name:
                                flat_entities.append({
                                    "name": ent_name,
                                    "type": std_type,
                                    "context_snippet": ent.get("context_snippet", "")
                                })
                        elif isinstance(ent, str) and ent.strip():
                            flat_entities.append({
                                "name": ent.strip(),
                                "type": std_type,
                                "context_snippet": ""
                            })

                for ent in flat_entities:
                    if not ent["name"]:
                        continue
                    graph_store.create_entity_node(
                        name=ent["name"],
                        type=ent["type"],
                        properties={"context_snippet": ent["context_snippet"]}
                    )
                    entities_created += 1

                    graph_store.create_relationship(
                        from_name=ent["name"],
                        to_name=doc_name,
                        rel_type="MENTIONED_IN",
                        properties={
                            "chunk_index": chunk.metadata.get("chunk_index", 0),
                            "chunk_id": chunk.metadata.get("chunk_id", "")
                        }
                    )
                    relationships_created += 1

                if flat_entities:
                    extracted_rels = extract_relationships(text, flat_entities, llm_client)
                    for rel in extracted_rels:
                        from_ent = rel.get("from_entity")
                        to_ent = rel.get("to_entity")
                        rel_type = rel.get("relationship_type")
                        if from_ent and to_ent and rel_type:
                            props = {}
                            if rel.get("date"):
                                props["date"] = rel.get("date")
                            if rel.get("quarter"):
                                props["quarter"] = rel.get("quarter")
                            graph_store.create_relationship(
                                from_name=from_ent,
                                to_name=to_ent,
                                rel_type=rel_type,
                                properties=props
                            )
                            relationships_created += 1

            neo4j_status = "populated"
    except Exception as e:
        print(f"[WARNING] Graph entity extraction skipped or failed: {e}")

    _notify("completed", 100, "Ingestion and knowledge graph extraction complete.")
    stat = path.stat()
    return {
        "doc_id": doc.metadata.get("doc_id", "unknown"),
        "filename": path.name,
        "file_path": str(path),
        "file_size_bytes": stat.st_size,
        "chunks_count": len(chunks),
        "created_at": _safe_isoformat(stat.st_mtime),
        "neo4j_status": neo4j_status,
        "entities_created": entities_created,
        "relationships_created": relationships_created,
        "status": "processed"
    }

import json

TAGS_STORE_PATH = Path(__file__).parent.parent.parent / "data" / "document_tags.json"

def get_document_tags() -> Dict[str, List[str]]:
    """Loads document tags from JSON storage."""
    if not TAGS_STORE_PATH.exists():
        return {}
    try:
        with open(TAGS_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] Failed to load document tags: {e}")
        return {}

def save_document_tags(filename: str, tags: List[str]) -> List[str]:
    """Updates and saves tags for a specific document filename."""
    TAGS_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_tags = get_document_tags()
    # Normalize tags: clean whitespace, lowercase, unique
    clean_tags = list(dict.fromkeys([t.strip().lower() for t in tags if t.strip()]))
    all_tags[filename] = clean_tags
    try:
        with open(TAGS_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(all_tags, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save document tags: {e}")
    return clean_tags

def get_all_documents() -> List[Dict[str, Any]]:
    """Retrieves metadata of all documents currently saved in data/documents."""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    supported_extensions = {".pdf", ".txt", ".md", ".docx", ".xlsx", ".xls", ".csv"}
    doc_tags_map = get_document_tags()

    # Retrieve vector store chunk counts grouped by filename
    chunk_counts = {}
    try:
        vector_store = ChromaVectorStore()
        # Query peek to count chunks per document source
        raw_results = vector_store.collection.get(include=["metadatas"])
        if raw_results and raw_results.get("metadatas"):
            for meta in raw_results["metadatas"]:
                if meta and "source" in meta:
                    source_name = meta["source"]
                    chunk_counts[source_name] = chunk_counts.get(source_name, 0) + 1
    except Exception as e:
        print(f"[WARNING] Failed to fetch Chroma chunk counts: {e}")

    docs_list = []
    for file in DOCUMENTS_DIR.rglob("*"):
        if file.is_file() and file.suffix.lower() in supported_extensions:
            try:
                stat = file.stat()
                mtime_str = _safe_isoformat(stat.st_mtime)
                c_count = chunk_counts.get(file.name, 0)
                file_tags = doc_tags_map.get(file.name, [])
                docs_list.append({
                    "doc_id": f"doc_{file.name}",
                    "filename": file.name,
                    "file_path": str(file.resolve()),
                    "file_size_bytes": stat.st_size,
                    "chunks_count": c_count,
                    "created_at": mtime_str,
                    "status": "processed" if c_count > 0 else "pending",
                    "tags": file_tags
                })
            except Exception as e:
                print(f"[ERROR] Failed to inspect document file {file}: {e}")

    # Sort by created_at descending (newest first), safely handling any missing timestamps
    docs_list.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return docs_list

