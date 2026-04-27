from pathlib import Path
from core.logger import get_logger
from core.config import Settings
from services.ingestion.loaders import load_documents_from_directory
from services.ingestion.chunking import chunk_documents
from services.retrieval.vector_store import create_vector_store

logger = get_logger(__name__)

def reindex_knowledge_base(settings: Settings):
    """
    Synchronously re-indexes the knowledge base by loading documents, 
    chunking them, and updating the vector store.
    """
    logger.info("Starting knowledge base re-indexing...")
    try:
        # Resolve the data/raw directory relative to this file
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        source_dir = root_dir / "data" / "raw"
        
        if not source_dir.exists():
            logger.warning("Source directory %s does not exist. Skipping reindex.", source_dir)
            return 0

        # 1. Load documents
        raw_documents = load_documents_from_directory(str(source_dir))
        
        # 2. Chunk documents
        chunked_documents = chunk_documents(raw_documents, settings)
        
        # 3. Create and persist vector store
        create_vector_store(chunked_documents, settings)
        
        logger.info("Successfully reindexed %d chunks!", len(chunked_documents))
        return len(chunked_documents)
    except Exception as e:
        logger.error("Error during re-indexing: %s", e)
        raise e
