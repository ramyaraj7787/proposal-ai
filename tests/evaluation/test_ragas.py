from services.evaluation.ragas_eval import evaluate_generation


def test_ragas_eval_reports_counts() -> None:
    metrics = evaluate_generation({"proposal_sections": [], "citations": []})
    assert metrics == {"section_count": 0, "citation_count": 0}
