# services/generation/prompt_optimizer.py

"""
Adjust LLM prompts dynamically based on historical user feedback.

Strategy
--------
1. Parse free-text *comments* to detect recurring quality themes.
2. Use the rating (positive / negative) as a weight signal.
3. Append targeted guidance blocks only when issues are clearly signalled
   — avoiding noisy, over-specified prompts when feedback is clean.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Theme detection keyword sets
# ---------------------------------------------------------------------------

_THEME_SIGNALS: dict[str, list[str]] = {
    "specificity": [
        "generic", "vague", "too broad", "not specific", "unclear",
        "lacks detail", "more detail", "more specific", "concrete",
    ],
    "evidence": [
        "no evidence", "unsupported", "no data", "no examples",
        "lacks evidence", "more evidence", "cite", "reference",
        "justify", "source",
    ],
    "structure": [
        "structure", "flow", "order", "disorganized", "hard to follow",
        "confusing", "layout", "format",
    ],
    "tone": [
        "tone", "too formal", "too casual", "language", "wording",
        "reads like", "sounds like",
    ],
    "brevity": [
        "too long", "verbose", "wordy", "shorten", "concise",
        "shorter", "repetitive", "repeated",
    ],
}

_THEME_GUIDANCE: dict[str, str] = {
    "specificity": (
        "- Be highly specific: reference exact deliverables, platforms, and "
        "constraints from the RFP rather than writing in general terms."
    ),
    "evidence": (
        "- Ground every claim in retrieved historical evidence or explicit "
        "RFP language. Do not make assertions without supporting context."
    ),
    "structure": (
        "- Follow a clear, logical flow: problem → solution → evidence → "
        "outcome. Ensure slide transitions are coherent."
    ),
    "tone": (
        "- Maintain a professional, consulting-grade tone throughout. "
        "Avoid colloquialisms and overly promotional language."
    ),
    "brevity": (
        "- Keep bullets concise (≤ 15 words each). Remove redundant "
        "phrases and avoid repeating the same point across slides."
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def adjust_prompt(base_prompt: str, feedback_history: list[dict]) -> str:
    """
    Return *base_prompt* augmented with targeted guidance derived from
    the user's prior feedback comments and ratings.

    Args:
        base_prompt:      The original prompt template string (already
                          formatted except for the ``{feedback_guidance}``
                          placeholder, if present).
        feedback_history: List of feedback dicts loaded from the JSONL
                          store.  Each entry has at minimum a ``"rating"``
                          key (``"positive"`` | ``"negative"``) and an
                          optional ``"comment"`` key.

    Returns:
        The original prompt unchanged when feedback is absent or
        consistently positive.  Otherwise the prompt with an appended
        ``FEEDBACK-DRIVEN GUIDANCE`` block.
    """
    if not feedback_history:
        return base_prompt

    negative_count = sum(
        1 for f in feedback_history if f.get("rating") == "negative"
    )

    # Collect comments only from negative entries (weighted 2×) plus all
    # comments generally (weighted 1×) to surface recurring themes.
    comment_corpus = ""
    for entry in feedback_history:
        comment = (entry.get("comment") or "").lower()
        if not comment:
            continue
        if entry.get("rating") == "negative":
            comment_corpus += f" {comment} {comment}"  # weight negatives 2×
        else:
            comment_corpus += f" {comment}"

    # Detect which quality themes are mentioned in the corpus
    triggered_themes: list[str] = []
    for theme, keywords in _THEME_SIGNALS.items():
        if any(kw in comment_corpus for kw in keywords):
            triggered_themes.append(theme)

    # Fall back to the old count-based heuristic for the specificity theme
    # when comments are absent but negative ratings accumulate.
    if not triggered_themes and negative_count > 5:
        triggered_themes.append("specificity")

    if not triggered_themes:
        return base_prompt

    guidance_lines = "\n".join(
        _THEME_GUIDANCE[theme] for theme in triggered_themes
    )
    guidance_block = (
        "\n\nFEEDBACK-DRIVEN GUIDANCE (based on prior user ratings):\n"
        f"{guidance_lines}"
    )

    return base_prompt + guidance_block


def build_feedback_summary(feedback_history: list[dict]) -> dict:
    """
    Produce a lightweight summary dict for display in the Streamlit UI.

    Returns keys: ``total``, ``positive``, ``negative``, ``themes``.
    """
    total = len(feedback_history)
    positive = sum(1 for f in feedback_history if f.get("rating") == "positive")
    negative = total - positive

    comment_corpus = " ".join(
        (f.get("comment") or "").lower() for f in feedback_history
    )
    themes = [
        theme
        for theme, keywords in _THEME_SIGNALS.items()
        if any(kw in comment_corpus for kw in keywords)
    ]

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "themes": themes,
    }