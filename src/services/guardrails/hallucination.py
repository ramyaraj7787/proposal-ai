"""Very light grounding-risk summary helpers."""


def summarize_grounding_risk(state: dict) -> str:
    """Return a compact grounding summary for downstream observability."""
    facts = state.get("rfp_facts", {})
    sections = state.get("proposal_sections", [])
    if facts and sections:
        return "rfp_facts_present_and_sections_generated"
    return "limited_grounding_signal"
