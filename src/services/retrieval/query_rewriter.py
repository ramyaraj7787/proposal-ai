"""Query rewriting helpers."""


def rewrite_query(query: str, rfp_fact_summary: str = "") -> str:
    """Bias retrieval toward extracted RFP facts while keeping the original query."""
    if rfp_fact_summary:
        return f"{query}\n{rfp_fact_summary}"
    return query
