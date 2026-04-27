# services/evaluation/metrics.py
"""Simple evaluation metrics for pipeline smoke tests."""

# def section_count(proposal_sections: list[dict[str, str]]) -> int:
#     """Return the number of generated proposal sections."""
#     return len(proposal_sections)


# def citation_count(citations: list[str]) -> int:
#     """Return the number of retrieval citations."""
#     return len(citations)

def compute_basic_metrics(state):
    """
    Lightweight evaluation (fast, no external deps)
    Replace with RAGAS later if needed.
    """

    sections = state.get("proposal_sections", [])
    context = state.get("retrieved_context", [])

    # Simple heuristics (fast + useful)
    faithfulness = min(1.0, len(context) / 5)
    relevance = min(1.0, len(sections) / 8)
    completeness = min(1.0, len(sections) / 10)

    return {
        "faithfulness": round(faithfulness, 2),
        "relevance": round(relevance, 2),
        "completeness": round(completeness, 2),
        "sections_count": len(sections),
        "retrieved_chunks": len(context),
    }