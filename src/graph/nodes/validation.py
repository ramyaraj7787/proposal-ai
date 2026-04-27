"""Validation and guardrail nodes."""

from graph.agents.critic import critic_review
from graph.state import ProposalState
from services.guardrails.hallucination import summarize_grounding_risk
from services.guardrails.validation import ensure_sections_present


def build_validation_node():
    """Return the node that performs light validation before PPT export."""

    def validation_node(state: ProposalState) -> ProposalState:
        state = critic_review(state)
        ensure_sections_present(state.get("proposal_sections", []))
        state["validation_summary"] = summarize_grounding_risk(state)
        return state

    return validation_node
