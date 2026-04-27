import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core.logger import get_logger
from core.config import get_settings
from services.ingestion.loaders import load_documents_from_directory
from services.ingestion.chunking import chunk_documents
from services.retrieval.vector_store import create_vector_store

logger = get_logger(__name__)

class ReindexEventHandler(FileSystemEventHandler):
    """
    Watches a directory for changes and triggers a reindex.
    Uses debouncing to prevent multiple rebuilds when multiple files are dropped at once.
    """
    def __init__(self, debounce_seconds: int = 5):
        self.debounce_seconds = debounce_seconds
        self._timer = None
        self._settings = get_settings()

    def on_created(self, event):
        if not event.is_directory:
            logger.info("File created: %s. Scheduling reindex...", event.src_path)
            self._schedule_reindex()

    def on_modified(self, event):
        if not event.is_directory:
            logger.info("File modified: %s. Scheduling reindex...", event.src_path)
            self._schedule_reindex()

    def _schedule_reindex(self):
        if self._timer is not None:
            self._timer.cancel()
        
        self._timer = threading.Timer(self.debounce_seconds, self._do_reindex)
        self._timer.start()

    def _do_reindex(self):
        logger.info("Starting background re-indexing of historical files...")
        try:
            root_dir = Path(__file__).resolve().parent.parent.parent.parent
            source_dir = root_dir / "data" / "raw"
            if not source_dir.exists():
                logger.warning("Source directory %s does not exist. Skipping reindex.", source_dir)
                return

            raw_documents = load_documents_from_directory(str(source_dir))
            chunked_documents = chunk_documents(raw_documents, self._settings)
            create_vector_store(chunked_documents, self._settings)
            logger.info("Successfully reindexed %d chunks in the background!", len(chunked_documents))
        except Exception as e:
            logger.error("Error during background re-indexing: %s", e)


def start_folder_watcher() -> Observer:
    """
    Starts the watchdog observer on the data/raw directory.
    Returns the observer instance so it can be stopped later.
    """
    settings = get_settings()
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    watch_dir = root_dir / "data" / "raw"
    watch_dir.mkdir(parents=True, exist_ok=True)
    
    event_handler = ReindexEventHandler()
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()
    
    logger.info("Started watching %s for new files to reindex.", watch_dir)
    return observer
