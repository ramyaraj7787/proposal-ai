from services.generation.proposal_generator import _parse_sections


def test_parse_sections_reads_expected_blocks() -> None:
    response = """
SLIDE_KEY: slide_1
SLIDE_TITLE: Proposed Solution
- Build a modular AI proposal platform.
---
SLIDE_KEY: slide_2
SLIDE_TITLE: Why Us
- Reusable assets and governed delivery.
---
"""
    sections = _parse_sections(response)
    assert len(sections) == 2
    assert sections[0]["title"] == "Proposed Solution"
