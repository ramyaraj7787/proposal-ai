"""RFP parsing nodes."""

from graph.state import ProposalState
from services.ingestion.rfp_parser import parse_rfp
from services.generation.proposal_generator import extract_rfp_facts, summarize_rfp


def build_parse_rfp_node():
    """Return the node that parses the uploaded RFP into text."""

    def parse_rfp_node(state: ProposalState) -> ProposalState:
        state["rfp_text"] = parse_rfp(state["rfp_path"])
        return state

    return parse_rfp_node


def build_extract_rfp_facts_node(settings):
    """Return the node that extracts structured facts from the RFP."""

    def extract_rfp_facts_node(state: ProposalState) -> ProposalState:
        rfp_facts, rfp_fact_summary = extract_rfp_facts(state["rfp_text"], settings)
        state["rfp_facts"] = rfp_facts
        state["rfp_fact_summary"] = rfp_fact_summary
        return state

    return extract_rfp_facts_node


def build_summarize_node(settings):
    """Return the node that builds the executive summary and retrieval query."""

    def summarize_node(state: ProposalState) -> ProposalState:
        executive_summary, retrieval_query = summarize_rfp(state["rfp_text"], settings)
        state["executive_summary"] = executive_summary
        state["retrieval_query"] = retrieval_query or state["rfp_text"][:500]
        return state

    return summarize_node
