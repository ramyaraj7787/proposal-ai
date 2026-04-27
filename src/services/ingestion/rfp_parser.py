"""Helpers for parsing and persisting uploaded RFP files."""

from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from services.ingestion.loaders import load_text_from_file


def parse_rfp(file_path: str) -> str:
    """Convert a supported RFP file into plain text."""
    return load_text_from_file(file_path)


def build_rfp_preview(file_path: str, max_chars: int = 1500) -> str:
    """Return a compact preview of the parsed RFP for UI validation."""
    text = parse_rfp(file_path)
    compact = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return compact[:max_chars]


def save_uploaded_file(upload: BinaryIO, output_dir: Path) -> Path:
    """Persist an uploaded file to the working output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = output_dir / f"{timestamp}_{upload.name}"
    with destination.open("wb") as file_handle:
        file_handle.write(upload.getbuffer())
    return destination
