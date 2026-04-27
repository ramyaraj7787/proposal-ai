"""FAISS vector store creation and loading utilities."""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from core.config import Settings
from services.llm.ollama_factory import build_embedding_model


def build_or_load_vector_store(settings: Settings) -> FAISS:
    """Load a persisted FAISS store for similarity search."""
    embeddings = build_embedding_model(settings)
    index_path = settings.vector_store_path
    if Path(index_path).exists():
        # LangChain persists FAISS locally, so load the latest saved index.
        return FAISS.load_local(
            str(index_path),
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )
    raise FileNotFoundError(
        f"Vector store not found at {index_path}. Run scripts/index_documents.py first."
    )


def create_vector_store(documents: list[Document], settings: Settings) -> FAISS:
    """Create and persist a FAISS store from indexed documents."""
    embeddings = build_embedding_model(settings)
    # Build the index once during ingestion and reuse it during proposal generation.
    vector_store = FAISS.from_documents(documents=documents, embedding=embeddings)
    vector_store.save_local(str(settings.vector_store_path))
    return vector_store
