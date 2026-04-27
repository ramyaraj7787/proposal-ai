"""Very light grounding-risk summary helpers."""

from core.logger import get_logger

logger = get_logger(__name__)


def summarize_grounding_risk(state: dict) -> str:
    """Return a compact grounding summary for downstream observability."""
    facts = state.get("rfp_facts", {})
    sections = state.get("proposal_sections", [])
    if facts and sections:
        result = "rfp_facts_present_and_sections_generated"
    else:
        result = "limited_grounding_signal"
    logger.info("Grounding risk verdict: %s", result)
    return result
