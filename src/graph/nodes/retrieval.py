"""Retrieval nodes for context and template resolution."""

from graph.state import ProposalState
from services.retrieval.retrieval_service import (
    retrieve_context,
    retrieve_template_outline,
)
from services.retrieval.query_rewriter import rewrite_query


def build_retrieve_node(settings):
    """Return the node that retrieves evidence and template outline."""

    def retrieve_node(state: ProposalState) -> ProposalState:
        query = rewrite_query(state["retrieval_query"], state.get("rfp_fact_summary", ""))
        retrieved_context, citations = retrieve_context(query, settings)
        template_source, template_slides = retrieve_template_outline(query, settings)
        state["retrieved_context"] = retrieved_context
        state["citations"] = citations
        state["template_source"] = template_source
        state["template_slides"] = template_slides
        return state

    return retrieve_node
