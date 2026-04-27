from services.evaluation.ragas_eval import evaluate_generation


def test_pipeline_metrics_smoke() -> None:
    result = {
        "proposal_sections": [{"title": "Executive Summary", "content": "Example."}],
        "citations": ["template.pptx (slide 2: Executive Summary)"],
    }
    metrics = evaluate_generation(result)
    assert metrics["section_count"] == 1
    assert metrics["citation_count"] == 1
