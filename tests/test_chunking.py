from core.config import Settings
from services.ingestion.chunking import chunk_documents


def test_chunking_keeps_source_metadata() -> None:
    settings = Settings(max_chunk_size=50, chunk_overlap=10)
    docs = [
        {
            "text": "A" * 130,
            "source": "sample.docx",
            "metadata": {"filename": "sample.docx", "extension": ".docx"},
        }
    ]
    chunks = chunk_documents(docs, settings)
    assert len(chunks) > 1
    assert chunks[0].metadata["source"] == "sample.docx"
    assert "chunk_id" in chunks[0].metadata
