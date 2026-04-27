"""Factories for Ollama chat and embedding models."""

from langchain_ollama import ChatOllama, OllamaEmbeddings

from core.config import Settings


def build_chat_model(settings: Settings) -> ChatOllama:
    """Create the chat model used for reasoning and text generation."""
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_chat_model,
        temperature=0.2,
    )


def build_embedding_model(settings: Settings) -> OllamaEmbeddings:
    """Create the embedding model used for indexing and retrieval."""
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embed_model,
    )
