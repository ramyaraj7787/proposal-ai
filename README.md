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
├── .dockerignore                         # Excludes unnecessary files from Docker builds
├── .env.example                          # Template for environment variables
├── .gitignore                            # Files/folders ignored by Git 
├── app.py                                # Streamlit UI entry point for the application
├── docker-compose.yml                    # Multi-container setup (if extended)
├── Dockerfile                            # Container definition for the app
├── LICENSE                               # Open-source license
├── pyproject.toml                        # Project dependencies and build configuration
├── pyrightconfig.json                    # Static type checking configuration (Pyright)
├── README.md                             # Project documentation

├── core/                                 # Core infrastructure utilities
│   ├── config.py                         # Settings loader (env + defaults)
│   ├── constants.py                      # Global constants (app name, prompts, etc.)
│   ├── logger.py                         # Centralized logging setup
│   └── __init__.py

├── data/                                 # Data layer (partially ignored in Git)
│   ├── .gitkeep                          # Ensures folder is tracked
│   │
│   ├── generated/                        # Generated outputs (ignored except structure)
│   │   ├── .gitkeep
│   │   ├── *.pptx                        # Generated proposal decks
│   │   └── uploads/                      # Uploaded RFP files
│   │       └── *.pdf
│   │
│   ├── raw/                              # Static input assets
│   │   ├── .gitkeep
│   │   ├── Proposal.pptx                 # Sample proposal
│   │   └── template.pptx                 # Base template used for generation
│   │
│   └── vector_store/                     # Vector database storage (FAISS)
│       ├── .gitkeep
│       └── proposal_faiss/
│           ├── index.faiss               # Vector index
│           └── index.pkl                 # Metadata mapping

├── src/                                  # Main application source code
│
│   ├── graph/                            # LangGraph orchestration layer
│   │   ├── builder.py                    # Builds and compiles the workflow graph
│   │   ├── state.py                      # Shared state definition across nodes
│   │   │
│   │   ├── agents/                       # Multi-agent components
│   │   │   ├── critic.py                 # Evaluates generated output 
│   │   │   ├── planner.py                # Determines structure/strategy
│   │   │
│   │   └── nodes/                        # Execution nodes in the pipeline
│   │       ├── parse.py                  # RFP parsing node
│   │       ├── retrieval.py              # Retrieval + reranking logic
│   │       ├── generation.py             # Proposal section generation
│   │       ├── validation.py             # Validation + retry routing
│   │       └── ppt.py                    # PPT generation node
│
│   ├── schemas/                          # Data models
│   │   └── state_schema.py               # Input/output schema for pipeline
│
│   ├── scripts/                          # Utility scripts
│   │   ├── index_documents.py            # Builds vector store from documents
│   │   └── evaluate_pipeline.py          # Runs evaluation pipeline
│
│   └── services/                         # Core business logic
│
│       ├── evaluation/                   # Evaluation + feedback loop
│       │   ├── metrics.py                # Lightweight evaluation metrics
│       │   ├── ragas_eval.py             # Advanced RAG evaluation (optional)
│       │   └── feedback_store.py         # Stores user feedback
│
│       ├── generation/                   # Proposal generation logic
│       │   ├── proposal_generator.py     # Main generation pipeline
│       │   ├── prompt_templates.py       # LLM prompts
│       │   └── prompt_optimizer.py       # Feedback-driven prompt tuning
│
│       ├── guardrails/                   # Safety + validation
│       │   ├── hallucination.py          # Detect hallucinations
│       │   └── validation.py             # Output validation rules
│
│       ├── ingestion/                    # Data ingestion pipeline
│       │   ├── loaders.py                # File loaders (PDF/DOCX/TXT)
│       │   ├── chunking.py               # Text chunking for RAG
│       │   ├── preprocess.py             # File preprocessing + saving
│       │   └── rfp_parser.py             # RFP text extraction
│
│       ├── llm/                          # LLM abstraction
│       │   └── ollama_factory.py         # Local LLM interface (Ollama)
│
│       ├── ppt/                          # Output generation
│       │   └── ppt_builder.py            # Builds PowerPoint slides
│
│       └── retrieval/                    # RAG layer
│           ├── vector_store.py           # FAISS interaction
│           ├── retrieval_service.py      # Retrieval pipeline
│           └── query_rewriter.py         # Query optimization
│
└── tests/                                # Test suite
    ├── unit/                             # Unit tests
    │   ├── test_chunking.py
    │   └── test_section_parser.py
    │
    ├── integration/                      # End-to-end pipeline tests
    │   └── test_pipeline.py
    │
    └── evaluation/                       # Evaluation tests
        └── test_ragas.py
```

## Setup

1. Create and activate a virtual environment:

```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies (this reads from `pyproject.toml`):

```bash
pip install -e .
```

3. Start Ollama and pull the required local models:

```bash
ollama pull mistral:7b
ollama pull nomic-embed-text
```

4. Create the vector index from historical content:

```bash
python src/scripts/index_documents.py --source_dir data/raw
```

If you change the ingestion logic or add new proposal decks, rebuild the FAISS index so the latest slide-level content is searchable.

5. Launch the UI:

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
