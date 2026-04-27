"""Shared Pydantic and TypedDict schemas."""

from typing import Any, TypedDict

from pydantic import BaseModel, Field


class ProposalInput(BaseModel):
    """Input payload captured before graph execution."""

    rfp_path: str
    country: str
    sector: str
    domain: str
    client: str
    proposal_objective: str
    assistant_prompt: str = (
        "Emphasize business impact, delivery credibility, and differentiators."
    )


class ProposalSection(BaseModel):
    """Generated proposal section stored as slide title plus content."""

    title: str
    content: str


class RetrievedContext(BaseModel):
    """Normalized retrieval result returned from the vector store."""

    text: str
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProposalState(TypedDict, total=False):
    """Shared LangGraph state."""

    rfp_path: str
    country: str
    sector: str
    domain: str
    client: str
    proposal_objective: str
    assistant_prompt: str
    rfp_text: str
    rfp_facts: dict[str, str | list[str]]
    rfp_fact_summary: str
    executive_summary: str
    retrieval_query: str
    retrieved_context: list[dict[str, Any]]
    template_source: str
    template_slides: list[dict[str, Any]]
    citations: list[str]
    gap_analysis: list[str]
    improvement_recommendations: list[str]
    proposal_sections: list[dict[str, str]]
    ppt_output_path: str
    # critic / validation fields
    critic_feedback: list[str]
    needs_retry: bool
    retry_count: int
    validation_summary: str
