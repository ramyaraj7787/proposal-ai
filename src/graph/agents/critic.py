"""Simple graph critic hooks."""


def critic_review(state):
    """
    Evaluates generated sections and flags issues.
    """

    sections = state.get("proposal_sections", [])
    context = state.get("retrieved_context", [])

    issues = []

    if len(sections) < 3:
        issues.append("Too few sections generated")

    for sec in sections:
        if len(sec["content"]) < 50:
            issues.append(f"Section '{sec['title']}' is too short")

    # naive hallucination check
    if not context:
        issues.append("No supporting context used")

    state["critic_feedback"] = issues
    state["needs_retry"] = len(issues) > 0

    return state

def validation_router(state):
    """
    Decide whether to retry generation or proceed.
    """

    retry_count = state.get("retry_count", 0)

    if state.get("needs_retry") and retry_count < 2:
        state["retry_count"] = retry_count + 1
        return "retry"

    return "proceed"
