"""FAISS vector store creation and loading utilities."""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from core.config import Settings
from core.logger import get_logger
from services.llm.ollama_factory import build_embedding_model

logger = get_logger(__name__)


def build_or_load_vector_store(settings: Settings) -> FAISS:
    """Load a persisted FAISS store for similarity search."""
    embeddings = build_embedding_model(settings)
    index_path = settings.vector_store_path
    if Path(index_path).exists():
        logger.info("Loading vector store from %s", index_path)
        return FAISS.load_local(
            str(index_path),
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )
    logger.error("Vector store not found at %s", index_path)
    raise FileNotFoundError(
        f"Vector store not found at {index_path}. Run scripts/index_documents.py first."
    )


def create_vector_store(documents: list[Document], settings: Settings) -> FAISS:
    """Create and persist a FAISS store from indexed documents."""
    embeddings = build_embedding_model(settings)
    logger.info("Building vector store from %d documents", len(documents))
    vector_store = FAISS.from_documents(documents=documents, embedding=embeddings)
    vector_store.save_local(str(settings.vector_store_path))
    logger.info("Vector store saved to %s", settings.vector_store_path)
    return vector_store
