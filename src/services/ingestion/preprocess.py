"""Preprocessing helpers for uploaded RFP assets."""

from pathlib import Path
from typing import BinaryIO

from services.ingestion.rfp_parser import build_rfp_preview, parse_rfp, save_uploaded_file


def preprocess_upload(upload: BinaryIO, output_dir: Path) -> Path:
    """Persist an uploaded file and return its saved path."""
    return save_uploaded_file(upload, output_dir)


__all__ = ["build_rfp_preview", "parse_rfp", "preprocess_upload", "save_uploaded_file"]
