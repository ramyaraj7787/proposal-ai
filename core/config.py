"""Application configuration helpers."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Default path to the PowerPoint template
DEFAULT_TEMPLATE_PATH = Path("data/template/template.pptx")


class Settings(BaseSettings):
    """
    Runtime configuration for:
    - Local LLM (Ollama)
    - Embedding model
    - Vector store
    - Output directories
    - Chunking and retrieval parameters
    """

    model_config = SettingsConfigDict(
        env_file=".env",                # Load variables from .env file
        env_file_encoding="utf-8",     # Encoding of .env file
        extra="ignore",               # Ignore unknown env variables
    )

    # Base URL for the local Ollama server
    ollama_base_url: str = Field(default="http://localhost:11434")

    # Chat model used for generation
    # ollama_chat_model: str = Field(default="llama3.1:8b")
    ollama_chat_model: str = Field(default="mistral:7b")

    # Embedding model used for vector representation
    ollama_embed_model: str = Field(default="nomic-embed-text")

    # Path where FAISS vector store is stored
    vector_store_path: Path = Field(default=Path("data/vector_store/proposal_faiss"))

    # Directory where generated outputs (e.g., PPTs) will be saved
    output_dir: Path = Field(default=Path("data/generated"))

    # Preferred PowerPoint template path (updated location)
    preferred_template_path: Path = Field(default=DEFAULT_TEMPLATE_PATH)

    # Maximum size of each text chunk (used in RAG pipeline)
    max_chunk_size: int = Field(default=1000)

    # Overlap between chunks to preserve context
    chunk_overlap: int = Field(default=150)

    # Number of top relevant results to retrieve from vector store
    top_k_results: int = Field(default=3)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached Settings instance and ensures required directories exist.
    """

    settings = Settings()

    # Ensure output directory exists
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure parent directory for vector store exists
    settings.vector_store_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure template directory exists (optional but safer)
    settings.preferred_template_path.parent.mkdir(parents=True, exist_ok=True)

    return settings
