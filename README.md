# Project Chronos: Self-Correcting Temporal Enterprise Analyst

Project Chronos is a self-correcting, temporal-aware GraphRAG (Graph Retrieval-Augmented Generation) system for enterprise business intelligence. It combines vector search (ChromaDB) with structured relationship querying (Neo4j) and utilizes LLMs to extract entities, temporal metadata, and semantic associations to answer complex business queries.

---

## Key Features
* **UI Document Upload & Ingestion**: Direct drag-and-drop or single-click document upload (`.pdf`, `.docx`, `.xlsx`, `.csv`, `.txt`, `.md`) from the React frontend, automatically chunking text, generating embeddings into ChromaDB, and populating Neo4j entity graphs.
* **Document Status Cards**: Real-time sidebar status cards displaying file size, total chunk index count, created timestamp, and ingestion status.
* **Recursive Multi-Format Loader**: Supports PDF, Word Memos (`.docx`), Financial Spreadsheets (`.xlsx`, `.csv`), `.txt`, and `.md` formats, generating unique document MD5 hashes and capturing absolute temporal modification dates.
* **Semantic Vector Storage**: Chunks texts and embeds them using local `all-MiniLM-L6-v2` SentenceTransformers into a persistent ChromaDB instance.
* **Auto-Routing Entity Extraction**: Leverages OpenRouter's `openrouter/free` LLM router to flat-extract `people`, `companies`, `products`, `events`, and `metrics` from raw text chunks.
* **Knowledge Graph Construction**: Populates a local Neo4j database using transactional Cypher queries, linking entities together with temporal attributes (`date`, `quarter`) and anchoring them to document nodes via `MENTIONED_IN` relationships.
* **Self-Correcting LangGraph State Machine**: Grounded validation loop that automatically re-evaluates answers, rewrites low-confidence queries, and falls back to live web search when internal context is insufficient.
* **Multi-LLM Provider Engine & Failover**: Seamless runtime LLM switcher supporting OpenRouter (Primary) and Groq (Automatic Fallback). If OpenRouter rate limits or network issues occur, the pipeline automatically fails over to Groq without query interruption.
* **Document Tagging & Smart Search**: Real-time document filtering and instant tag management (`PUT /api/documents/tags`). Users can assign custom tags (`#finance`, `#q3-2024`, `#spec`) to ingested files, filter the knowledge base by tag pills, and perform smart search across filenames and tag metadata.
* **Auto-Suggested Related Questions**: Dynamically generates 3 contextual follow-up questions for every RAG query answer using LLM analysis. Users can click any suggestion to instantly execute the follow-up query with full session memory continuity.
* **Live Ingestion Progress Telemetry**: Real-time progress bar feedback during document uploads tracking each pipeline stage (document parsing → text chunking → vector embedding → ChromaDB indexing → Neo4j entity graph extraction).
* **Confidence Score History Dashboard**: Real-time telemetry dashboard displaying confidence score trends over time, grounded validation pass rates, self-correction iteration counts, and detailed query grounding audit trails.
* **Multi-Turn Conversation Memory**: Maintains context across follow-up queries within a session (e.g. *"What happened next?"* or *"Tell me more about that metric"*), with a dedicated session reset control.
* **Temporal Timeline Slider**: A dedicated "Timeline" tab in the frontend displaying chronological events extracted from documents across quarters and date attributes, with entity type filtering and deep event inspection.
* **Executive PDF & Word Report Exporter**: One-click generation of executive briefing reports containing synthesized RAG findings, confidence metrics, citation audit tables, and self-correction rewrite history exported in PDF (`.pdf`), Word (`.docx`), or Markdown (`.md`) formats.
* **Interactive Knowledge Graph Visualizer**: A dedicated "Knowledge Graph" view in the frontend built with pure HTML Canvas & a custom force simulation. Click any entity node (Company, Person, Product, Event, Metric) to inspect its connections and temporal relationship properties in real-time.

---

## Project Structure

```text
d:/Projects/Chronos Self Correcting Temporal Enterprise Analyst/
├── config/
│   ├── __init__.py
│   └── settings.py          # Application configurations loader (Pydantic)
├── data/
│   ├── documents/           # Source business memos and PDFs
│   ├── structured/          # Structured database templates
│   ├── chroma_db/           # Chroma Vector database files (git-ignored)
│   └── logs/                # Local runtime logs and query history (git-ignored)
├── frontend/                # React + Vite + TS + Tailwind frontend
│   ├── src/                 # React components, document cards, and layouts
│   ├── package.json         # Node package configuration
│   └── tailwind.config.js   # Tailwind style overrides
├── src/
│   ├── api/                 # FastAPI routes (query, ingest, health, documents, history)
│   ├── ingestion/           # Pipeline: loader, chunker, embedder, vector store, ingest runner
│   ├── retrieval/           # Retrieval strategies (vector, keyword, hybrid)
│   ├── generation/          # Self-correcting answer generation logic
│   ├── workflow/            # LangGraph workflow orchestration
│   ├── graph/               # Graph pipeline: entity extractor, neo4j client, populator
│   └── utils/               # Shared helpers (LLM openrouter client)
├── tests/                   # Test suite
├── .env.example             # Template for API keys & DB passwords
├── .gitignore               # Standard git-ignore rules (ignores .env, build outputs, node_modules)
├── main.py                  # Initial scaffolding test script
├── run_api.py               # Root runner to start FastAPI Uvicorn server
├── run_ingestion.py         # Ingestion pipeline CLI
├── run_graph_population.py  # Graph population pipeline CLI
└── requirements.txt         # Project dependencies
```

---

## Getting Started

### Prerequisites
* **Python 3.10+** (tested on Python 3.13)
* **Node.js 18+**
* **Docker Desktop** (to run Neo4j locally)

### 1. Set Up the Project
Clone this repository and navigate to the project directory:
```bash
git clone https://github.com/tejaspatel2255/chronos-temporal-graph-rag.git
cd chronos-temporal-graph-rag
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
```
* **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Database Setup (Neo4j via Docker)
Start the Neo4j instance in the background using Docker:
```bash
docker run -d --name neo4j-chronos -p 7474:7474 -p 7687:7687 -v neo4j_data:/data -e NEO4J_AUTH=neo4j/password123 neo4j:latest
```

### 5. Configuration Setup
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your OpenRouter API key:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
NEO4J_PASSWORD=password123
```

---

## Running the Pipelines & Web Application

### FastAPI Web Service
Start the local API development server with the virtual environment:
```powershell
.\venv\Scripts\python.exe run_api.py
```
This runs the API on `http://localhost:8000`.

#### Interactive Documentation
Once the API is running, you can access:
* **Interactive Swagger UI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Alternative Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### Key API Endpoints
* **`POST /api/ingest`**: Upload and process documents into vector store and graph database with live progress updates.
* **`GET /api/ingest/progress`**: Stream or poll live progress telemetry during active document ingestion pipelines.
* **`PUT /api/documents/tags`**: Assign or update custom classification tags on ingested documents.
* **`POST /api/query`**: Execute a query through the self-correcting RAG pipeline (accepts custom parameter `force_fallback: bool`).
* **`GET /api/health`**: Inspect server status, Neo4j connectivity, Chroma document ingest counts, and active LLM provider.
* **`GET /api/history`**: Get a list of execution events from the local JSONL query log.
* **`GET /api/analytics/confidence`**: Get aggregated confidence score analytics, grounding pass rate, and recent telemetry history.
* **`DELETE /api/chat/session/{session_id}`**: Clear multi-turn conversation memory for a specific chat session.
* **`GET /api/graph`**: Returns all Neo4j entity nodes and relationships for the interactive knowledge graph visualizer.
* **`GET /api/timeline`**: Returns chronological temporal events extracted from Neo4j for the timeline visualizer.
* **`GET /api/providers`**: List all configured LLM providers and their active/configured status.
* **`POST /api/providers/switch`**: Switch the active primary LLM provider at runtime without restarting the server.

---

### React Web Frontend

A modern, responsive React web application under `frontend/` allows running queries and uploading documents visually.

#### Running the Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
This launches the application on `http://localhost:3000`.

---

## GitHub Security & Safe Pushing

To ensure proprietary credentials, API keys, or databases are protected, the following rules are enforced in `.gitignore`:

1. **API Keys & Secrets (`.env` & `frontend/.env*`):** Any `.env` file containing `OPENROUTER_API_KEY`, database passwords, or endpoint paths is ignored. **Never commit `.env` files.**
2. **Databases (`data/chroma_db/`):** The binary database files storing vector indexes are ignored. Only `data/chroma_db/.gitkeep` is tracked.
3. **Execution History (`data/logs/`):** Local query run logs (`query_log.jsonl`) generated during queries are excluded.
4. **Node Modules & Dev Builds (`node_modules/`, `dist/`, `build/`):** All local frontend compilation dependencies are excluded.
