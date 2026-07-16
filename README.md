# Project Chronos: Self-Correcting Temporal Enterprise Analyst

Project Chronos is a self-correcting, temporal-aware GraphRAG (Graph Retrieval-Augmented Generation) system for enterprise business intelligence. It combines vector search (ChromaDB) with structured relationship querying (Neo4j) and utilizes LLMs to extract entities, temporal metadata, and semantic associations to answer complex business queries.

---

## Key Features (Phases 0-2)
* **Recursive Document Loader**: Supports PDF, `.txt`, and `.md` formats, generating unique document MD5 hashes and capturing absolute temporal modification dates.
* **Semantic Vector Storage**: Chunks texts and embeds them using local `all-MiniLM-L6-v2` SentenceTransformers into a persistent ChromaDB instance.
* **Auto-Routing Entity Extraction**: Leverages OpenRouter's `openrouter/free` LLM router to flat-extract `people`, `companies`, `products`, `events`, and `metrics` from raw text chunks.
* **Knowledge Graph Construction**: Populates a local Neo4j database using transactional Cypher queries, linking entities together with temporal attributes (`date`, `quarter`) and anchoring them to document nodes via `MENTIONED_IN` relationships.

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
│   ├── src/                 # React components and layouts
│   ├── package.json         # Node package configuration
│   └── tailwind.config.js   # Tailwind style overrides
├── src/
│   ├── api/                 # FastAPI routes and Pydantic schemas
│   ├── ingestion/           # Vector pipeline: loader, chunker, embedder, vector store
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
* **Python 3.10+**
* **Docker Desktop** (to run Neo4j locally)

### 1. Set Up the Project
Clone this repository and navigate to the project directory:
```bash
git clone https://github.com/YOUR_USERNAME/chronos-temporal-rag.git
cd chronos-temporal-rag
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

## Running the Pipelines

### Phase 1: Vector Ingestion
Run the vector pipeline to ingest sample documents into the Chroma Vector Database:
```bash
python run_ingestion.py
```
To verify vector retrieval:
```bash
python verify_retrieval.py
```

### Phase 2: Graph Population
Run the graph pipeline to extract semantic entity networks and populate Neo4j:
```bash
python run_graph_population.py
```
This script will output the created node distribution count and display verified Cypher relationship paths for verification.

---

## FastAPI Web Service (Phase 7)

A FastAPI web service is available to wrap the LangGraph RAG pipeline.

### Running the API
Start the local API development server:
```bash
python run_api.py
```
This runs the API on `http://localhost:8000`.

### Documentation
Once the API is running, you can access:
* **Interactive Swagger UI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Alternative Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### API Endpoints
* **`POST /api/query`**: Run a query through the self-correcting RAG pipeline (accepts custom parameter `force_fallback: bool`).
* **`GET /api/health`**: Inspect server status, Neo4j connectivity, and Chroma document ingest counts.
* **`GET /api/history`**: Get a list of the last N execution events from the local JSONL query log.

---

## React Web Frontend (Phase 8)

A modern, responsive React web application is available under `frontend/` to run queries visually.

### Running the Frontend
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

To ensure you do not leak proprietary credentials, API keys, or databases to public repositories, the following rules have been set up in `.gitignore`:

1. **API Keys & Secrets (`.env` & `frontend/.env*`):** Any `.env` file containing `OPENROUTER_API_KEY`, database passwords, or endpoint paths is ignored. **Never commit `.env` files.**
2. **Databases (`data/chroma_db/`):** The binary database files storing vector indexes are ignored. Only `data/chroma_db/.gitkeep` is tracked.
3. **Execution History (`data/logs/`):** Local query run logs (`query_log.jsonl`) generated during queries are excluded.
4. **Node Modules & Dev Builds (`node_modules/`, `dist/`, `build/`):** All local frontend compilation dependencies are excluded.


