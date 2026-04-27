"""Lightweight planning helper for graph execution."""


def build_execution_plan() -> list[str]:
    """Return the default graph execution sequence."""
    return [
        "parse_rfp",
        "extract_rfp_facts",
        "summarize",
        "retrieve_context",
        "gap_analysis",
        "generate_sections",
        "recommend_improvements",
        "validate_sections",
        "build_ppt",
    ]
