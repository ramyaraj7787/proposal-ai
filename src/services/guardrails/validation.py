"""Validation helpers for generated proposal sections."""


def ensure_sections_present(proposal_sections: list[dict[str, str]]) -> None:
    """Raise a clear error if no proposal sections were produced."""
    if not proposal_sections:
        raise ValueError("No proposal sections were generated.")
