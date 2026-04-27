"""Placeholder RAG evaluation helpers."""

from services.evaluation.metrics import citation_count, section_count


def evaluate_generation(result: dict) -> dict[str, int]:
    """Return lightweight structural metrics for a generated proposal."""
    return {
        "section_count": section_count(result.get("proposal_sections", [])),
        "citation_count": citation_count(result.get("citations", [])),
    }
