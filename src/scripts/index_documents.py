import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.config import get_settings
from services.ingestion.chunking import chunk_documents
from services.ingestion.loaders import load_documents_from_directory
from services.retrieval.vector_store import create_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Index proposal documents into FAISS.")
    parser.add_argument("--source_dir", required=True, help="Directory containing proposal assets")
    args = parser.parse_args()

    settings = get_settings()
    raw_documents = load_documents_from_directory(args.source_dir)
    chunked_documents = chunk_documents(raw_documents, settings)
    create_vector_store(chunked_documents, settings)
    print(f"Indexed {len(chunked_documents)} chunks into {settings.vector_store_path}")


if __name__ == "__main__":
    main()
