"""Generation nodes for proposal content."""

from graph.state import ProposalState
from services.generation.proposal_generator import (
    analyze_gaps,
    generate_sections,
    recommend_improvements,
)


def build_gap_analysis_node(settings):
    """Return the node that analyzes RFP gaps and risks."""

    def gap_analysis_node(state: ProposalState) -> ProposalState:
        state["gap_analysis"] = analyze_gaps(
            rfp_text=state["rfp_text"],
            retrieved_context=state["retrieved_context"],
            settings=settings,
        )
        return state

    return gap_analysis_node


def build_section_generation_node(settings):
    """Return the node that generates proposal sections."""

    def section_generation_node(state: ProposalState) -> ProposalState:
        state["proposal_sections"] = generate_sections(state, settings)
        return state

    return section_generation_node


def build_improvement_node(settings):
    """Return the node that suggests proposal improvements."""

    def improvement_node(state: ProposalState) -> ProposalState:
        state["improvement_recommendations"] = recommend_improvements(
            rfp_text=state["rfp_text"],
            retrieved_context=state["retrieved_context"],
            settings=settings,
        )
        return state

    return improvement_node
