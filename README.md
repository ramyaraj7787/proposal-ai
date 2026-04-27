# AI-Driven Proposal Development Tool
An AI-powered accelerator that converts uploaded RFPs into consultant-ready proposal decks by combining RFP parsing, RAG with FAISS-based enterprise knowledge search, and LangGraph-orchestrated workflows using local LLMs. It also incorporates evaluation, human feedback loops, and automated PowerPoint generation for high-quality outputs.

## Why this solution stands out

- Uses a proper Retrieval-Augmented Generation pipeline to ingest historical proposals, templates, and case studies across `DOCX`, `PDF`, and `PPTX`.
- Stores reusable knowledge in a local `FAISS` vector index for fast retrieval and easy on-prem deployment.
- Orchestrates the workflow with `LangGraph`, which makes the generation process traceable, extensible, and easy to govern.
- Uses `Ollama` for local LLMs so the design works even in enterprise environments with strict data boundaries.
- Produces consultant-ready `PowerPoint` output, not just plain text, directly matching the case-study requirement.
- Includes a simple `Streamlit` UI for uploading an RFP and capturing business metadata like country, sector, domain, and client.

## Target architecture

1. `Ingestion Layer`
   Reads raw proposals, templates, and case studies from a repository.
2. `Knowledge Layer`
   Chunks, enriches, and indexes content into `FAISS`.
3. `Orchestration Layer`
   Runs a `LangGraph` workflow for parsing, retrieval, gap analysis, drafting, and slide generation.
4. `Generation Layer`
   Uses `Ollama` models for reasoning, retrieval grounding, and content generation.
5. `Delivery Layer`
   Exports a structured `.pptx` proposal deck and traceable rationale.

## Project structure

```text
.
|-- app.py
|-- pyproject.toml
|-- .env.example
|-- core/
|   |-- config.py
|   `-- constants.py
|-- docs/
|   `-- submission_notes.md
|-- src/
|   |-- graph/
|   |-- schemas/
|   |-- scripts/
|   |   `-- index_documents.py
|   `-- services/
`-- tests/
```

## Setup

1. Install dependencies:

```bash
pip install -e .
```

2. Start Ollama and pull the required local models:

```bash
ollama pull mistral:7b
ollama pull nomic-embed-text
```

3. Create the vector index from historical content:

```bash
python src/scripts/index_documents.py --source_dir data/raw
```

If you change the ingestion logic or add new proposal decks, rebuild the FAISS index so the latest slide-level content is searchable.

4. Launch the UI:

```bash
streamlit run app.py
```

## Docker Setup

If you prefer to run the application in a Docker container, you can use the provided `Dockerfile` and `docker-compose.yml`. This setup assumes you still have Ollama running locally on your host machine to leverage hardware acceleration.

1. Create the vector index locally first (or configure it to mount):
```bash
python src/scripts/index_documents.py --source_dir data/raw
```

2. Start the container using Docker Compose:
```bash
docker-compose up -d --build
```

The application will be available at `http://localhost:8501`. The `data/` directory is mounted as a volume so your vector index and generated outputs persist.

## Demo flow

1. Upload an RFP document.
2. Provide metadata such as country, sector, domain, and client.
3. Run the proposal generation workflow.
4. Review:
   - retrieved source references
   - identified risks and gaps
   - generated proposal slides grounded in retrieved historical proposal decks
   - exported PowerPoint path

## Enterprise-readiness notes

- Local-model compatible for confidential proposal data.
- Modular components allow future swap-out to Azure OpenAI or internal embedding services.
- LangGraph state transitions make the workflow observable and governable.
- Retrieval output is explainable because every generated section keeps linked evidence snippets.
