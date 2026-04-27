RFP_FACTS_PROMPT = """
You are extracting proposal-relevant facts from an RFP.
Use only the RFP text below. Do not invent missing information.

RFP TEXT:
{rfp_text}

Return exactly in this format:
PROJECT_NAME: <value or NOT_FOUND>
CLIENT_NAME: <value or NOT_FOUND>
OBJECTIVE: <value or NOT_FOUND>
BUDGET: <value or NOT_FOUND>
DELIVERABLES:
- <deliverable 1>
- <deliverable 2>
PLATFORMS:
- <platform 1>
- <platform 2>
CONSTRAINTS:
- <constraint 1>
- <constraint 2>
TIMELINE: <value or NOT_FOUND>
ACCESSIBILITY:
- <requirement 1>
- <requirement 2>
FUTURE_SCOPE:
- <item 1>
- <item 2>
"""

RFP_SUMMARY_PROMPT = """
You are a senior AI consulting lead preparing for a proposal bid.
Read the RFP text and produce:
1. A concise executive summary
2. A retrieval query that will help find the most relevant historical proposal content

RFP TEXT:
{rfp_text}

Return in the following format:
EXEC_SUMMARY: <summary>
RETRIEVAL_QUERY: <query>
"""

GAP_ANALYSIS_PROMPT = """
You are reviewing an RFP to identify proposal gaps, delivery risks, missing assumptions, and areas where stronger differentiation is needed.
Use only the RFP as the source of truth.
{feedback_guidance}
RFP TEXT:
{rfp_text}

Return 5-7 bullet points, one per line, with no numbering.
"""

IMPROVEMENT_RECOMMENDATION_PROMPT = """
You are an AI proposal quality coach.
Review the RFP and the retrieved proposal evidence, then recommend improvements to:
1. Content quality
2. Proposal differentiation
3. Slide design/storytelling
4. Executive messaging
Use only the RFP as the source of truth.
{feedback_guidance}
RFP TEXT:
{rfp_text}

Return 4-6 bullet points, one per line, with no numbering.
"""

DECK_GENERATION_PROMPT = """
You are writing a consulting proposal deck.
Use the template slide list only as a structural reference for slide order and titles.
Do not copy the template wording. Write fresh content using the RFP as the primary source.
Do not infer the solution domain from the template. The uploaded RFP is the only source of proposal substance.

CLIENT: {client}
COUNTRY: {country}
SECTOR: {sector}
DOMAIN: {domain}
OBJECTIVE: {proposal_objective}
AUTHORING GUIDANCE: {assistant_prompt}
{feedback_guidance}
TEMPLATE SLIDES:
{template_slides}

RFP TEXT:
{rfp_text}

RFP FACTS:
{rfp_fact_summary}

KNOWN GAPS / RISKS:
{gap_analysis}

Write 3 to 4 concise bullets for each template slide.
Each bullet must be specific to the RFP and appropriate for the slide title.
Avoid placeholders, avoid meta commentary, and avoid repeating the same sentence structure.
If multiple slides have the same title, treat them as different slides.
Do not mention capabilities, systems, modules, or business context unless they are supported by the RFP text.

Return the result exactly in this format:
SLIDE_KEY: <unique slide key 1>
SLIDE_TITLE: <template title 1>
- bullet one
- bullet two
- bullet three
---
SLIDE_KEY: <unique slide key 2>
SLIDE_TITLE: <template title 2>
- bullet one
- bullet two
- bullet three
"""
