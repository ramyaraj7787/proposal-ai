"""Generation nodes for proposal content."""

from core.logger import get_logger
from graph.state import ProposalState
from services.generation.proposal_generator import (
    analyze_gaps,
    generate_sections,
    recommend_improvements,
)

logger = get_logger(__name__)


def build_gap_analysis_node(settings):
    """Return the node that analyzes RFP gaps and risks."""

    def gap_analysis_node(state: ProposalState) -> ProposalState:
        logger.info("Running gap analysis node")
        state["gap_analysis"] = analyze_gaps(
            rfp_text=state["rfp_text"],
            retrieved_context=state["retrieved_context"],
            settings=settings,
        )
        logger.info("Gap analysis complete: %d items", len(state["gap_analysis"]))
        return state

    return gap_analysis_node


def build_section_generation_node(settings):
    """Return the node that generates proposal sections."""

    def section_generation_node(state: ProposalState) -> ProposalState:
        logger.info("Running section generation node")
        state["proposal_sections"] = generate_sections(state, settings)
        logger.info("Section generation complete: %d sections", len(state["proposal_sections"]))
        return state

    return section_generation_node


def build_improvement_node(settings):
    """Return the node that suggests proposal improvements."""

    def improvement_node(state: ProposalState) -> ProposalState:
        logger.info("Running improvement recommendations node")
        state["improvement_recommendations"] = recommend_improvements(
            rfp_text=state["rfp_text"],
            retrieved_context=state["retrieved_context"],
            settings=settings,
        )
        logger.info("Improvement recommendations complete: %d items", len(state["improvement_recommendations"]))
        return state

    return improvement_node
