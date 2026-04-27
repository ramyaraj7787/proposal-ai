"""Validation and guardrail nodes."""

from core.logger import get_logger
from graph.agents.critic import critic_review
from graph.state import ProposalState
from services.guardrails.hallucination import summarize_grounding_risk
from services.guardrails.validation import ensure_sections_present

logger = get_logger(__name__)


def build_validation_node():
    """Return the node that performs light validation before PPT export."""

    def validation_node(state: ProposalState) -> ProposalState:
        logger.info("Running validation node")
        state = critic_review(state)
        ensure_sections_present(state.get("proposal_sections", []))
        state["validation_summary"] = summarize_grounding_risk(state)
        logger.info("Validation complete: %s", state["validation_summary"])
        return state

    return validation_node
