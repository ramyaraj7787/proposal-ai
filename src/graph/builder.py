"""LangGraph builder using split node modules."""

from langgraph.graph import END, StateGraph   

from graph.agents.planner import build_execution_plan
from graph.nodes.generation import (
    build_gap_analysis_node,
    build_improvement_node,
    build_section_generation_node,
)
from graph.nodes.parse import (
    build_extract_rfp_facts_node,
    build_parse_rfp_node,
    build_summarize_node,
)
from graph.nodes.ppt import build_ppt_node
from graph.nodes.retrieval import build_retrieve_node
from graph.nodes.validation import build_validation_node
from graph.state import ProposalState


def build_proposal_graph(settings):
    """Build and compile the end-to-end proposal workflow graph."""
    graph = StateGraph(ProposalState)

    graph.add_node("parse_rfp", build_parse_rfp_node())
    graph.add_node("extract_rfp_facts", build_extract_rfp_facts_node(settings))
    graph.add_node("summarize", build_summarize_node(settings))
    graph.add_node("retrieve_context", build_retrieve_node(settings))
    graph.add_node("gap_analysis", build_gap_analysis_node(settings))
    graph.add_node("generate_sections", build_section_generation_node(settings))
    graph.add_node("recommend_improvements", build_improvement_node(settings))
    graph.add_node("validate_sections", build_validation_node())
    graph.add_node("build_ppt", build_ppt_node(settings))

    plan = build_execution_plan()
    graph.set_entry_point(plan[0])
    graph.add_edge("parse_rfp", "extract_rfp_facts")
    graph.add_edge("extract_rfp_facts", "summarize")
    graph.add_edge("summarize", "retrieve_context")
    graph.add_edge("retrieve_context", "gap_analysis")
    graph.add_edge("gap_analysis", "generate_sections")
    graph.add_edge("generate_sections", "recommend_improvements")
    graph.add_edge("recommend_improvements", "validate_sections")
    graph.add_edge("validate_sections", "build_ppt")
    graph.add_edge("build_ppt", END)
    return graph.compile()
