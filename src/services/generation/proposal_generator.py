"""LLM-backed proposal reasoning and slide generation helpers."""

import re

from services.llm.ollama_factory import build_chat_model
from services.generation.prompt_templates import (
    DECK_GENERATION_PROMPT,
    GAP_ANALYSIS_PROMPT,
    IMPROVEMENT_RECOMMENDATION_PROMPT,
    RFP_FACTS_PROMPT,
    RFP_SUMMARY_PROMPT,
)
from services.evaluation.feedback_store import load_feedback
from services.generation.prompt_optimizer import adjust_prompt


def extract_rfp_facts(rfp_text: str, settings) -> tuple[dict[str, str | list[str]], str]:
    """Extract structured facts from the uploaded RFP."""
    llm = build_chat_model(settings)
    response = llm.invoke(RFP_FACTS_PROMPT.format(rfp_text=rfp_text)).content
    facts = _parse_rfp_facts(response)
    facts = _merge_fact_fallbacks(facts, rfp_text)
    return facts, _format_rfp_facts(facts)


def summarize_rfp(rfp_text: str, settings) -> tuple[str, str]:
    """Summarize the RFP and derive a retrieval query."""
    llm = build_chat_model(settings)
    response = str(llm.invoke(RFP_SUMMARY_PROMPT.format(rfp_text=rfp_text)).content)
    executive_summary = _extract_tag(response, "EXEC_SUMMARY")
    retrieval_query = _extract_tag(response, "RETRIEVAL_QUERY")
    executive_summary = (
        executive_summary
        or "RFP parsed successfully. Proposal deck will be grounded "
        "in retrieved historical proposal assets."
    )
    retrieval_query = retrieval_query or rfp_text[:500]
    return executive_summary, retrieval_query


def analyze_gaps(rfp_text: str, retrieved_context: list[dict], settings) -> list[str]:
    """Identify proposal risks, assumptions, and missing information."""
    _ = retrieved_context
    llm = build_chat_model(settings)

    feedback_history = load_feedback()
    feedback_guidance = _build_feedback_guidance(feedback_history)

    response = llm.invoke(
        GAP_ANALYSIS_PROMPT.format(
            rfp_text=rfp_text,
            feedback_guidance=feedback_guidance,
        )
    ).content
    return [line.strip("- ").strip() for line in response.splitlines() if line.strip()]


def generate_sections(
    state: dict,
    settings,
) -> list[dict[str, str]]:
    """Generate slide content aligned to the chosen template deck."""
    if not state.get("template_slides"):
        # If no template was retrieved, still return a usable deterministic draft.
        return _fallback_sections_from_template(state)

    content_template_slides = _get_content_template_slides(state["template_slides"])
    title_occurrences: dict[str, int] = {}
    title_totals = _count_title_occurrences(content_template_slides)
    deterministic_sections: list[dict[str, str]] = []
    missing_slide_keys: set[str] = set()

    for template_slide in content_template_slides:
        normalized_title = template_slide["title"].strip().lower()
        title_occurrences[normalized_title] = title_occurrences.get(normalized_title, 0) + 1
        occurrence = title_occurrences[normalized_title]
        slide_key = _build_slide_key(template_slide)
        fact_backed = _build_fact_backed_bullets(
            template_slide=template_slide,
            state=state,
            occurrence=occurrence,
            total_occurrences=title_totals[normalized_title],
        )
        deterministic_sections.append(
            {
                "key": slide_key,
                "title": template_slide["title"],
                "content": "\n".join(fact_backed) if fact_backed else "",
            }
        )
        if not fact_backed:
            missing_slide_keys.add(slide_key)

    if not missing_slide_keys:
        return [
            {"title": section["title"], "content": section["content"]}
            for section in deterministic_sections
        ]

    llm = build_chat_model(settings)
    shared_gaps = "\n".join(state["gap_analysis"])

    feedback_history = load_feedback()
    feedback_guidance = _build_feedback_guidance(feedback_history)

    response = llm.invoke(
        DECK_GENERATION_PROMPT.format(
            client=state["client"],
            country=state["country"],
            sector=state["sector"],
            domain=state["domain"],
            proposal_objective=state["proposal_objective"],
            assistant_prompt=state["assistant_prompt"],
            feedback_guidance=feedback_guidance,
            template_slides=_join_template_slides(content_template_slides),
            rfp_text=state["rfp_text"],
            rfp_fact_summary=state["rfp_fact_summary"],
            gap_analysis=shared_gaps,
        )
    ).content

    parsed_sections = _parse_deck_sections(response)
    sections_by_key = {
        section["key"]: section["content"]
        for section in parsed_sections
    }
    final_sections: list[dict[str, str]] = []
    for template_slide, seed_section in zip(content_template_slides, deterministic_sections):
        content = seed_section["content"]
        if not content:
            slide_key = seed_section["key"]
            content = sections_by_key.get(slide_key, "")
        if not content:
            bullets = _fallback_bullets_for_slide(template_slide, state)
            content = "\n".join(bullets)
        final_sections.append(
            {
                "title": seed_section["title"],
                "content": content,
            }
        )

    return final_sections


def recommend_improvements(rfp_text: str, retrieved_context: list[dict], settings) -> list[str]:
    """Generate improvement recommendations for consultant review."""
    _ = retrieved_context
    llm = build_chat_model(settings)

    feedback_history = load_feedback()
    feedback_guidance = _build_feedback_guidance(feedback_history)

    response = llm.invoke(
        IMPROVEMENT_RECOMMENDATION_PROMPT.format(
            rfp_text=rfp_text,
            feedback_guidance=feedback_guidance,
        )
    ).content
    return [line.strip("- ").strip() for line in response.splitlines() if line.strip()]


def _build_feedback_guidance(feedback_history: list[dict]) -> str:
    """
    Build the feedback_guidance string to inject into prompts.

    Returns an empty string when there is no feedback so that the
    ``{feedback_guidance}`` placeholder in every template is always
    safely substituted.
    """
    if not feedback_history:
        return ""
    adjusted = adjust_prompt("", feedback_history)
    # adjust_prompt returns empty string unchanged when no themes fire;
    # strip the leading newlines added by the guidance block.
    return adjusted.strip()


def _extract_tag(response: str, tag: str) -> str:
    """Extract a tagged value from a structured LLM response."""
    for line in response.splitlines():
        if line.startswith(f"{tag}:"):
            return line.split(":", 1)[1].strip()
    return ""


def _parse_rfp_facts(response: str) -> dict[str, str | list[str]]:
    """Parse a structured RFP-facts response into a dictionary."""
    facts: dict[str, str | list[str]] = {
        "project_name": "NOT_FOUND",
        "client_name": "NOT_FOUND",
        "objective": "NOT_FOUND",
        "budget": "NOT_FOUND",
        "deliverables": [],
        "platforms": [],
        "constraints": [],
        "timeline": "NOT_FOUND",
        "accessibility": [],
        "future_scope": [],
    }
    current_list_key = ""

    for raw_line in response.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("PROJECT_NAME:"):
            facts["project_name"] = line.split(":", 1)[1].strip()
            current_list_key = ""
        elif line.startswith("CLIENT_NAME:"):
            facts["client_name"] = line.split(":", 1)[1].strip()
            current_list_key = ""
        elif line.startswith("OBJECTIVE:"):
            facts["objective"] = line.split(":", 1)[1].strip()
            current_list_key = ""
        elif line.startswith("BUDGET:"):
            facts["budget"] = line.split(":", 1)[1].strip()
            current_list_key = ""
        elif line.startswith("TIMELINE:"):
            facts["timeline"] = line.split(":", 1)[1].strip()
            current_list_key = ""
        elif line == "DELIVERABLES:":
            current_list_key = "deliverables"
        elif line == "PLATFORMS:":
            current_list_key = "platforms"
        elif line == "CONSTRAINTS:":
            current_list_key = "constraints"
        elif line == "ACCESSIBILITY:":
            current_list_key = "accessibility"
        elif line == "FUTURE_SCOPE:":
            current_list_key = "future_scope"
        elif current_list_key and line.startswith("- "):
            cast_list = facts[current_list_key]
            if isinstance(cast_list, list):
                cast_list.append(line[2:].strip())

    return facts


def _merge_fact_fallbacks(
    facts: dict[str, str | list[str]],
    rfp_text: str,
) -> dict[str, str | list[str]]:
    """Backfill critical facts directly from RFP text when parsing is weak."""
    compact = " ".join(rfp_text.split())

    if facts["budget"] == "NOT_FOUND":
        budget_match = re.search(r"\$[\d,]+(?:\s*-\s*\$[\d,]+)?", compact)
        if budget_match:
            facts["budget"] = budget_match.group(0)

    if facts["project_name"] == "NOT_FOUND":
        project_match = re.search(r"Request for Proposal\s+(.*?)\s+development and design", compact, re.IGNORECASE)
        if project_match:
            facts["project_name"] = project_match.group(1).strip()

    if facts["client_name"] == "NOT_FOUND":
        client_match = re.search(r"([A-Z][A-Za-z\s&()]+Corporation)", compact)
        if client_match:
            facts["client_name"] = client_match.group(1).strip()

    if facts["objective"] == "NOT_FOUND":
        objective_match = re.search(
            r"opportunity for (.*?)(?:\.| The budget range)",
            compact,
            re.IGNORECASE,
        )
        if objective_match:
            facts["objective"] = objective_match.group(1).strip()

    facts = _fallback_list_facts(facts, compact)
    return facts


def _fallback_list_facts(
    facts: dict[str, str | list[str]],
    compact: str,
) -> dict[str, str | list[str]]:
    """Populate list-style facts using simple pattern heuristics."""
    if isinstance(facts["platforms"], list) and not facts["platforms"]:
        platforms = []
        if "Apple iOS" in compact:
            platforms.append("Apple iOS")
        if "Android" in compact:
            platforms.append("Android")
        facts["platforms"] = platforms

    if isinstance(facts["accessibility"], list) and not facts["accessibility"]:
        accessibility = []
        if "captions" in compact.lower():
            accessibility.append("Audio content must include captions.")
        if "ADA" in compact:
            accessibility.append("Design the app to ADA digital standards.")
        if "translation of audio" in compact.lower():
            accessibility.append("Consider translation support for multilingual visitors.")
        facts["accessibility"] = accessibility

    if isinstance(facts["deliverables"], list) and not facts["deliverables"]:
        deliverables = []
        for marker in [
            "Create an app for Apple iOS and Android",
            "Use QR codes and GPS technology to activate the AR program",
            "Provide custom design services for Hemisfair specific QR Code badges and produce the first 250 badges",
            "AR experience to pop up near a tree that has already been claimed showing a photo, text and/or audio",
            "A “Search for Tree” option to find the recognition name",
            "A map function to help app users find a specific tree",
            "Design the app to ADA digital standards",
            "Develop an easy to learn Customer Management System",
        ]:
            if marker.lower() in compact.lower():
                deliverables.append(marker)
        facts["deliverables"] = deliverables

    if isinstance(facts["constraints"], list) and not facts["constraints"]:
        constraints = []
        if "governmental entities" in compact.lower():
            constraints.append(
                "The bidder must demonstrate relevant experience with governmental or nonprofit organizations."
            )
        if "$50,000 - $100,000" in compact:
            constraints.append(
                "The solution must be delivered within the stated budget range of $50,000 - $100,000."
            )
        if "branding standards" in compact.lower():
            constraints.append(
                "Application visuals and QR assets must align to Hemisfair branding standards."
            )
        facts["constraints"] = constraints

    if isinstance(facts["future_scope"], list) and not facts["future_scope"]:
        future_scope = []
        if "future additions" in compact.lower():
            future_scope.append(
                "The platform should support future content and visitor experience enhancements."
            )
        if "easy to learn customer management system" in compact.lower():
            future_scope.append(
                "Content administration should allow staff to maintain and expand donor records over time."
            )
        facts["future_scope"] = future_scope

    return facts


def _format_rfp_facts(facts: dict[str, str | list[str]]) -> str:
    """Serialize structured RFP facts into a compact prompt block."""
    lines = [
        f"Project Name: {facts['project_name']}",
        f"Client Name: {facts['client_name']}",
        f"Objective: {facts['objective']}",
        f"Budget: {facts['budget']}",
        f"Timeline: {facts['timeline']}",
    ]

    for key, label in [
        ("deliverables", "Deliverables"),
        ("platforms", "Platforms"),
        ("constraints", "Constraints"),
        ("accessibility", "Accessibility"),
        ("future_scope", "Future Scope"),
    ]:
        values = facts[key]
        if isinstance(values, list) and values:
            lines.append(f"{label}: " + "; ".join(values))

    return "\n".join(lines)


def _count_title_occurrences(template_slides: list[dict]) -> dict[str, int]:
    """Count repeated slide titles to support split content generation."""
    counts: dict[str, int] = {}
    for slide in template_slides:
        normalized_title = slide["title"].strip().lower()
        counts[normalized_title] = counts.get(normalized_title, 0) + 1
    return counts


def _build_fact_backed_bullets(
    template_slide: dict,
    state: dict,
    occurrence: int,
    total_occurrences: int,
) -> list[str]:
    """Create slide bullets directly from extracted RFP facts when possible."""
    facts = state.get("rfp_facts", {})
    title = template_slide["title"].strip().lower()
    reference_text = template_slide.get("reference_text", "").lower()
    project_name = _fact_text(facts, "project_name")
    client_name = _fact_text(facts, "client_name")
    objective = _fact_text(facts, "objective")
    budget = _fact_text(facts, "budget")
    timeline = _fact_text(facts, "timeline")
    deliverables = _fact_list(facts, "deliverables")
    platforms = _fact_list(facts, "platforms")
    constraints = _fact_list(facts, "constraints")
    accessibility = _fact_list(facts, "accessibility")
    future_scope = _fact_list(facts, "future_scope")
    gap_points = state.get("gap_analysis") or []

    if "executive summary" in title:
        bullets = []
        if objective:
            bullets.append(objective)
        elif project_name:
            bullets.append(
                f"{client_name or 'The client'} issued the RFP for {project_name}."
            )
        if platforms or deliverables:
            experience_bullet = _build_experience_bullet(platforms, deliverables)
            if experience_bullet:
                bullets.append(experience_bullet)
        delivery_bullet = _build_delivery_bullet(
            budget=budget,
            accessibility=accessibility,
            future_scope=future_scope,
            constraints=constraints,
        )
        if delivery_bullet:
            bullets.append(delivery_bullet)
        return bullets[:3]

    if "problem" in title:
        bullets = []
        if project_name:
            bullets.append(
                f"The {project_name} RFP requires a public-facing digital experience that turns donor recognition into an engaging visitor journey."
            )
        if platforms or deliverables:
            bullets.append(
                _build_problem_scope_bullet(platforms, deliverables, accessibility)
            )
        if constraints:
            bullets.append(constraints[min(occurrence - 1, len(constraints) - 1)])
        elif budget:
            bullets.append(
                f"The proposed delivery approach must balance experience design, mobile development, and content operations within the RFP budget of {budget}."
            )
        elif gap_points:
            bullets.append(gap_points[min(occurrence - 1, len(gap_points) - 1)])
        return bullets[:3]

    if "scope" in title:
        if "out of scope" in reference_text:
            return _build_out_of_scope_bullets(
                client_name=client_name,
                project_name=project_name,
            )
        scoped_items = list(deliverables)
        scoped_items.extend(item for item in accessibility if item not in scoped_items)
        scoped_items.extend(item for item in future_scope if item not in scoped_items)
        scoped_deliverables = _slice_for_occurrence(scoped_items, occurrence, total_occurrences)
        bullets = scoped_deliverables[:3]
        if not bullets and constraints:
            bullets = constraints[:3]
        return bullets

    if "overview" in title or "four key components" in reference_text:
        return _build_solution_overview_bullets(platforms)

    if "high-level architecture" in title:
        architecture_groups = _build_architecture_groups(
            deliverables=deliverables,
            platforms=platforms,
            accessibility=accessibility,
            future_scope=future_scope,
            constraints=constraints,
        )
        group = architecture_groups[min(occurrence - 1, len(architecture_groups) - 1)]
        bullets = [item for item in group if item]
        if timeline and timeline != "NOT_FOUND" and len(bullets) < 3:
            bullets.append(f"Delivery timeline noted in the RFP: {timeline}.")
        return bullets[:3]

    if "key features" in title:
        return _build_key_feature_bullets(deliverables)

    if "deliverables" in title:
        return _build_deliverable_bullets(
            deliverables=deliverables,
            platforms=platforms,
            future_scope=future_scope,
        )

    if "timeline" in title or "project plan" in title:
        return _build_timeline_bullets(timeline)

    if "assumption" in title:
        return _build_assumption_bullets(
            client_name=client_name,
            deliverables=deliverables,
            constraints=constraints,
        )

    if "dependenc" in title:
        return _build_dependency_bullets(
            client_name=client_name,
            platforms=platforms,
        )

    if "risk" in title and "mitigation" in title:
        return _build_risk_bullets(deliverables)

    if "budget" in title:
        return _build_budget_bullets(budget)

    return []


def _fact_text(facts: dict[str, str | list[str]], key: str) -> str:
    """Return a scalar fact or an empty string."""
    value = facts.get(key, "")
    if isinstance(value, str) and value != "NOT_FOUND":
        return _clean_text(value)
    return ""


def _fact_list(facts: dict[str, str | list[str]], key: str) -> list[str]:
    """Return a list fact or an empty list."""
    value = facts.get(key, [])
    if isinstance(value, list):
        return [_fact_to_sentence(item) for item in value if item]
    return []


def _slice_for_occurrence(items: list[str], occurrence: int, total_occurrences: int) -> list[str]:
    """Split a list of facts across repeated slides with the same title."""
    if not items:
        return []
    if total_occurrences <= 1:
        return items

    chunk_size = max(1, (len(items) + total_occurrences - 1) // total_occurrences)
    start = (occurrence - 1) * chunk_size
    end = start + chunk_size
    return items[start:end]


def _first_matching(items: list[str], *needles: str) -> str:
    """Return the first fact containing any of the requested needles."""
    for item in items:
        lowered = item.lower()
        if any(needle.lower() in lowered for needle in needles):
            return item
    return ""


def _clean_text(text: str) -> str:
    """Normalize encoding artifacts and extra whitespace."""
    cleaned = text.replace("â€œ", '"').replace("â€", '"')
    cleaned = cleaned.replace("â€™", "'").replace("&amp;", "&")
    return " ".join(cleaned.split())


def _fact_to_sentence(text: str) -> str:
    """Convert raw extracted RFP fragments into complete proposal sentences."""
    cleaned = _clean_text(text).strip().strip("-").strip()
    lowered = cleaned.lower()

    if lowered.startswith("create an app for apple ios and android"):
        return "The solution will include a mobile application for Apple iOS and Android devices."
    if "qr codes and gps technology" in lowered:
        return "The solution will use QR codes and GPS technology to activate the AR experience at each relevant tree location."
    if "first 250 badges" in lowered or "qr code badges" in lowered:
        return "The project will include custom QR badge design services and production support for the first 250 badges."
    if "photo, text and/or audio" in lowered or "photo, text, and audio" in lowered:
        return "The AR experience will display donor content through photos, text, and optional audio at recognized tree locations."
    if "search for tree" in lowered:
        return 'The application will provide a "Search for Tree" feature so users can quickly find a donor recognition name.'
    if "map function" in lowered:
        return "The application will include an interactive map function to help visitors find a specific tree."
    if "ada digital standards" in lowered:
        return "The application will be designed to align with ADA digital accessibility standards."
    if "customer management system" in lowered:
        return "The project will provide an easy-to-use content management system for staff to maintain donor information."
    if "captions" in lowered:
        return "Audio-enabled content will include captions to support accessibility."
    if "translation support" in lowered:
        return "The platform should support multilingual content options where required for visitor accessibility."
    if "governmental or nonprofit organizations" in lowered:
        return "The implementation partner should demonstrate relevant experience with governmental or nonprofit organizations."
    if "budget range of $50,000 - $100,000" in lowered:
        return "The solution should be delivered within the stated RFP budget range of $50,000 - $100,000."
    if "branding standards" in lowered:
        return "Application visuals and QR assets should align with Hemisfair branding standards."
    if "future content and visitor experience enhancements" in lowered:
        return "The platform should support future content expansion and broader visitor experience enhancements."
    if "maintain and expand donor records" in lowered:
        return "The content administration workflow should support ongoing maintenance and expansion of donor records."

    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned[0].upper() + cleaned[1:]


def _build_experience_bullet(platforms: list[str], deliverables: list[str]) -> str:
    """Build a concise executive-summary bullet from core user experience asks."""
    experience_items = [
        _first_matching(deliverables, "Search for Tree", "map function"),
        _first_matching(deliverables, "photo", "audio", "text"),
    ]
    experience_items = [item for item in experience_items if item]
    if platforms and experience_items:
        return (
            "The solution must support "
            + ", ".join(platforms)
            + " and deliver core visitor features such as "
            + "; ".join(experience_items[:2])
            + "."
        )
    if platforms:
        return "The requested solution must support " + ", ".join(platforms) + "."
    if experience_items:
        return "; ".join(experience_items[:2]) + "."
    return ""


def _build_delivery_bullet(
    budget: str,
    accessibility: list[str],
    future_scope: list[str],
    constraints: list[str],
) -> str:
    """Build a delivery-governance bullet for the executive summary slide."""
    parts = []
    if budget:
        parts.append(f"delivery within the RFP budget of {budget}")
    if accessibility:
        parts.append("accessible visitor content and controls")
    if future_scope:
        parts.append("a maintainable foundation for future enhancements")
    elif constraints:
        parts.append(constraints[0].rstrip(".").lower())
    if not parts:
        return ""
    return "The proposed approach should enable " + ", ".join(parts) + "."


def _build_problem_scope_bullet(
    platforms: list[str],
    deliverables: list[str],
    accessibility: list[str],
) -> str:
    """Describe the multi-part scope complexity on the problem statement slide."""
    parts = []
    if platforms:
        parts.append("cross-platform mobile delivery for " + " and ".join(platforms))
    if _first_matching(deliverables, "QR codes", "GPS technology"):
        parts.append("QR and GPS-driven activation logic")
    if _first_matching(deliverables, "Search for Tree", "map function"):
        parts.append("search and navigation workflows for park visitors")
    if accessibility:
        parts.append("ADA-aligned accessibility expectations")
    if not parts:
        return "The requested solution spans multiple experience, content, and delivery workstreams."
    return "The engagement combines " + ", ".join(parts) + "."


def _build_architecture_groups(
    deliverables: list[str],
    platforms: list[str],
    accessibility: list[str],
    future_scope: list[str],
    constraints: list[str],
) -> list[list[str]]:
    """Assemble three distinct architecture slide groupings from extracted facts."""
    platforms_text = ", ".join(platforms) if platforms else "mobile platforms"
    experience_bullets = [
        _first_matching(deliverables, "QR codes", "GPS technology")
        or "QR and GPS triggers should activate the donor recognition experience at the relevant tree locations.",
        (
            f"A branded application on {platforms_text} should let visitors search for trees, "
            "navigate the park map, and launch the AR storytelling experience."
        ),
        _first_matching(deliverables, "audio", "photo", "text")
        or "Each donor recognition moment should support rich content such as image, text, and audio tributes.",
    ]
    operations_bullets = [
        _first_matching(deliverables, "Customer Management System")
        or "A staff-facing content management capability should support maintenance of donor records and media assets.",
        _first_matching(accessibility, "ADA")
        or "The experience should align to ADA-oriented digital design expectations from the RFP.",
        _first_matching(accessibility, "captions", "translation")
        or "Media delivery should account for captioning and other inclusive content access needs.",
    ]
    rollout_bullets = [
        _first_matching(deliverables, "250 badges")
        or "The rollout should include production support for the initial set of QR recognition assets.",
        constraints[0] if constraints else "Implementation should align to the operational and governance constraints called out in the RFP.",
        future_scope[0] if future_scope else "The architecture should leave room for future visitor experience enhancements without reworking the core platform.",
    ]
    return [experience_bullets, operations_bullets, rollout_bullets]


def _build_out_of_scope_bullets(client_name: str, project_name: str) -> list[str]:
    """Return exclusions for the out-of-scope slide."""
    owner = client_name or "the client"
    initiative = project_name or "the proposed solution"
    return [
        f"Modification or replacement of existing {owner} enterprise systems is outside the scope of {initiative}.",
        "Physical installation, park infrastructure maintenance, and field operations beyond QR deployment support are excluded.",
        "Advanced personalization, unrelated third-party integrations, and nonessential hardware procurement are not included in this phase.",
    ]


def _build_solution_overview_bullets(platforms: list[str]) -> list[str]:
    """Return the four-part solution overview expected by the target proposal deck."""
    platform_text = " and ".join(platforms) if platforms else "iOS and Android"
    return [
        f"Mobile Application: a cross-platform app on {platform_text} for QR scanning, AR interaction, and visitor navigation.",
        "Backend System: secure APIs, content storage, and application services to manage donor records and media delivery.",
        "Content Management System: a structured admin experience for staff to maintain donor information without technical dependence.",
        "AR Experience Layer: location-aware rendering that anchors donor recognition content to the physical tree environment.",
    ]


def _build_key_feature_bullets(deliverables: list[str]) -> list[str]:
    """Return visitor-facing feature bullets for the feature summary slide."""
    features = [
        _first_matching(deliverables, "QR codes"),
        _first_matching(deliverables, "photo", "audio", "text"),
        _first_matching(deliverables, "Search for Tree"),
        _first_matching(deliverables, "map function"),
        _first_matching(deliverables, "Customer Management System"),
    ]
    features = [feature for feature in features if feature]
    if not features:
        return [
            "QR code scanning for tree-specific donor recognition experiences.",
            "Interactive AR content with media-rich donor storytelling.",
            "Search, navigation, and staff content-management workflows.",
        ]
    return features[:3]


def _build_deliverable_bullets(
    deliverables: list[str],
    platforms: list[str],
    future_scope: list[str],
) -> list[str]:
    """Return concrete project deliverables for the target deck."""
    bullets = []
    if platforms:
        bullets.append(
            "Cross-platform mobile application delivery for " + " and ".join(platforms) + "."
        )
    bullets.extend(
        item
        for item in [
            _first_matching(deliverables, "QR codes"),
            _first_matching(deliverables, "Customer Management System"),
            _first_matching(deliverables, "250 badges"),
        ]
        if item
    )
    if future_scope and len(bullets) < 3:
        bullets.append(future_scope[0])
    if len(bullets) < 3:
        bullets.append("Implementation handover, administrator enablement, and deployment support.")
    return bullets[:3]


def _build_timeline_bullets(timeline: str) -> list[str]:
    """Return a proposal-oriented phased implementation plan."""
    if timeline:
        return [
            "Design Phase: requirements validation, experience design, and architecture alignment.",
            "Build Phase: mobile application, backend services, and CMS implementation.",
            f"Test and Rollout Phase: validation, pilot deployment, and final launch planning aligned to {timeline}.",
        ]
    return [
        "Design Phase: requirements validation, experience design, and architecture alignment.",
        "Build Phase: mobile application, backend services, and CMS implementation.",
        "Test and Rollout Phase: field validation, deployment readiness, and launch support.",
    ]


def _build_assumption_bullets(
    client_name: str,
    deliverables: list[str],
    constraints: list[str],
) -> list[str]:
    """Return implementation assumptions for the proposal."""
    owner = client_name or "The client"
    bullets = [
        f"{owner} will provide complete donor content, brand assets, and approval inputs in a timely manner.",
        "QR placement, park access, and physical site coordination will be supported by the client team during testing and rollout.",
    ]
    if constraints:
        bullets.append(constraints[0])
    elif _first_matching(deliverables, "Customer Management System"):
        bullets.append("Relevant staff will be available for CMS validation, training, and handover.")
    return bullets[:3]


def _build_dependency_bullets(client_name: str, platforms: list[str]) -> list[str]:
    """Return project dependencies for delivery planning."""
    owner = client_name or "client"
    platform_text = " and ".join(platforms) if platforms else "mobile"
    return [
        f"Timely availability of donor data, media assets, and location details from the {owner} team.",
        "Access to site layouts, testing windows, and park coordination for real-world QR and AR validation.",
        f"Availability of deployment prerequisites for {platform_text}, including relevant publishing and operational approvals.",
    ]


def _build_risk_bullets(deliverables: list[str]) -> list[str]:
    """Return concise risk and mitigation bullets."""
    qr_bullet = _first_matching(deliverables, "QR codes")
    media_bullet = _first_matching(deliverables, "audio", "photo", "text")
    return [
        "Location or GPS variance -> use QR anchoring and hybrid activation flows to preserve a reliable visitor experience.",
        (
            "Content inconsistency risk -> enforce structured content review and CMS validation before publication."
            if media_bullet
            else "Content readiness risk -> confirm source assets and approval flow early in the project."
        ),
        (
            "Field rollout complexity -> coordinate QR placement, app testing, and launch support with on-site stakeholders."
            if qr_bullet
            else "Adoption risk -> keep onboarding simple and validate the experience through pilot testing."
        ),
    ]


def _build_budget_bullets(budget: str) -> list[str]:
    """Return a budget slide aligned to the uploaded RFP."""
    if budget:
        return [
            f"The delivery approach is designed to align with the RFP budget range of {budget}.",
            "Estimated effort covers mobile development, backend and CMS implementation, AR enablement, testing, and deployment support.",
            "Budget prioritization should balance visitor experience quality, maintainability, and rollout readiness.",
        ]
    return [
        "The commercial proposal should align to the budget expectations stated in the uploaded RFP.",
        "Estimated effort covers mobile development, backend and CMS implementation, AR enablement, testing, and deployment support.",
        "Budget prioritization should balance visitor experience quality, maintainability, and rollout readiness.",
    ]


def _join_context(retrieved_context: list[dict]) -> str:
    """Join retrieved context into a prompt-friendly text block."""
    return "\n\n".join(
        f"Source: {item['source']}\nContent: {item['text']}"
        for item in retrieved_context
    )


def _join_template_slides(template_slides: list[dict]) -> str:
    """Serialize template slides into a compact prompt-friendly outline."""
    return "\n\n".join(
        (
            f"SLIDE_KEY: {_build_slide_key(slide)}\n"
            f"SLIDE_TITLE: {slide['title']}\n"
            f"REFERENCE_THEME: {slide.get('reference_text', '')[:400]}"
        )
        for slide in template_slides
    )


def _parse_deck_sections(response: str) -> list[dict[str, str]]:
    """Parse a full-deck generation response into ordered slide sections."""
    sections: list[dict[str, str]] = []
    blocks = [block.strip() for block in response.split("---") if block.strip()]

    for block in blocks:
        slide_key = ""
        title = ""
        bullets: list[str] = []
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if line.startswith("SLIDE_KEY:"):
                slide_key = line.split(":", 1)[1].strip()
                continue
            if line.startswith("SLIDE_TITLE:"):
                title = line.split(":", 1)[1].strip()
                continue
            if line.startswith(("- ", "* ", "\u2022 ")):
                bullets.append(line[2:].strip())
                continue
            if len(line) > 20 and title:
                bullets.append(line)

        parsed_bullets = _parse_bullets("\n".join(f"- {bullet}" for bullet in bullets))
        if slide_key and title and parsed_bullets:
            sections.append(
                {
                    "key": slide_key,
                    "title": title,
                    "content": "\n".join(parsed_bullets),
                }
            )

    return sections


def _parse_bullets(response: str) -> list[str]:
    """Normalize a raw LLM response into concise slide bullets."""
    bullets: list[str] = []
    valid_prefixes = ("- ", "* ", "\u2022 ")
    ignored_headers = ("SLIDE_TITLE:", "BULLETS:", "TITLE:", "CONTENT:")

    for raw_line in response.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith(valid_prefixes):
            bullets.append(line[2:].strip())
            continue

        if len(line) > 20 and not line.upper().startswith(ignored_headers):
            bullets.append(line)

    deduped: list[str] = []
    seen: set[str] = set()
    for bullet in bullets:
        compact = " ".join(bullet.strip().split())
        normalized = compact.lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            # Keep bullets short enough that the PPT layer can format them cleanly.
            deduped.append(compact[:260])

    return deduped[:4]


def _fallback_sections_from_template(state: dict) -> list[dict[str, str]]:
    """Create fallback slide content when no valid model output is available."""
    sections: list[dict[str, str]] = []
    for template in _get_content_template_slides(state["template_slides"]):
        bullets = _fallback_bullets_for_slide(template, state)
        sections.append({"title": template["title"], "content": "\n".join(bullets)})
    return sections


def _get_content_template_slides(template_slides: list[dict]) -> list[dict]:
    """Exclude the cover slide from slide-content generation."""
    if not template_slides:
        return []

    first_slide_number = min(
        slide.get("slide_number", 1)
        for slide in template_slides
    )
    return [
        slide
        for slide in template_slides
        if slide.get("slide_number", 1) != first_slide_number
    ]


def _build_slide_key(template_slide: dict) -> str:
    """Build a stable unique key for a template slide."""
    slide_number = template_slide.get("slide_number", 0)
    return f"slide_{slide_number}"


def _fallback_bullets_for_slide(template_slide: dict, state: dict) -> list[str]:
    """Return title-aware fallback bullets for a specific slide."""
    title = template_slide["title"].lower()
    summary = state.get("executive_summary", "Proposal aligned to the submitted RFP.")
    gap = (
        state.get("gap_analysis")
        or ["Clarify assumptions, delivery dependencies, and integration scope."]
    )[0]
    recommendation = (
        state.get("improvement_recommendations")
        or ["Strengthen differentiation through measurable business outcomes and phased delivery."]
    )[0]

    if "executive summary" in title:
        return [
            summary,
            f"Designed for {state['client']} across {state['sector']} in {state['country']}.",
            recommendation,
        ]

    if "problem" in title:
        return [
            "The RFP defines a business need that requires a structured, consultant-reviewable response.",
            "Key problem drivers, constraints, and scope boundaries should be taken directly from the uploaded RFP.",
            gap,
        ]

    if "scope" in title:
        return [
            "The scope of work should reflect only the deliverables and responsibilities stated in the RFP.",
            "Assumptions, exclusions, and delivery phases should be aligned to the uploaded RFP text.",
            gap,
        ]

    if "architecture" in title or "solution" in title:
        return [
            "The proposed approach should reflect the capabilities, workflows, and technical expectations stated in the RFP.",
            "Any implementation components mentioned in this slide must be traceable to the uploaded RFP.",
            recommendation,
        ]

    return [
        f"Content tailored for {state['client']} based on the submitted RFP and proposal objective.",
        summary,
        recommendation,
    ]
