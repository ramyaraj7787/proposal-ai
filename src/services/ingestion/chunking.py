"""Chunking helpers for retrieval indexing."""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import Settings


def chunk_documents(raw_documents: list[dict], settings: Settings) -> list[Document]:
    """Split loaded documents into retrieval-friendly chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunked_docs: list[Document] = []

    for item in raw_documents:
        chunks = splitter.split_text(item["text"])
        for idx, chunk in enumerate(chunks):
            metadata = dict(item["metadata"])
            metadata.update({"source": item["source"], "chunk_id": idx})
            chunked_docs.append(Document(page_content=chunk, metadata=metadata))

    return chunked_docs
