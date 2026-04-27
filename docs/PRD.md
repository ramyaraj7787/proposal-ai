# Product Requirements & Specification Document

## 1. Document Control

### 1.1 Document Title
Product Requirements & Specification Document for `AI-Driven Proposal Development Tool`

### 1.2 Purpose
This document defines the product vision, problem statement, target users, functional requirements, non-functional requirements, workflows, acceptance criteria, and delivery roadmap for the `AI-Driven Proposal Development Tool`.

## 2. Product Overview

### 2.1 Product Vision
Create an AI-enabled proposal acceleration platform that helps consultants turn unstructured RFPs into consultant-reviewable proposal decks faster, with stronger reuse of institutional knowledge, better consistency, differentiated recommendations, and an ongoing loop for human feedback.

### 2.2 Product Summary
The application ingests historical proposal content, templates, and case studies from a document repository, indexes them into a `FAISS` vector store, and uses `LangGraph` plus `Ollama` models to generate a new proposal deck grounded in the current RFP. The generated output is a `.pptx` proposal draft aligned to a retrieved reference deck structure. The application is Dockerized for simple enterprise evaluation and features an evaluation dashboard capturing consultant feedback.

## 3. Problem Statement

Consulting teams face recurring pain points during proposal creation:
- historical proposal assets are available but difficult to search and reuse quickly
- proposal teams waste time assembling storyline, structure, and content from disparate prior materials
- content reuse often becomes manual copy-paste, which introduces inconsistency and outdated messaging
- stakeholders need consultant-reviewable outputs, not raw LLM text responses
- **New Focus**: AI outputs degrade if unchecked; teams need transparency over quality metrics and the ability to give direct feedback.

## 4. Goals and Objectives

### 4.1 Business Goals
- reduce time to first proposal draft
- improve reuse of historical proposal assets
- improve consistency of proposal structure and messaging
- capture continuous human-in-the-loop feedback to iteratively improve prompts
- support confidential enterprise usage through local model deployment via Docker

### 4.2 Product Goals
- allow users to upload an RFP and generate a draft proposal deck
- use stored historical decks and templates as structural references
- generate slide content from the current RFP rather than copying old decks
- compute and display quantitative metrics (Faithfulness, Relevance, Completeness)
- capture thumbs up/down and written feedback from users on generated outputs
- export the output in PowerPoint format
- containerize via Docker Compose

## 5. Scope

### 5.1 In Scope
- RFP upload in `PDF`, `DOCX`, or `TXT`
- metadata capture such as country, sector, domain, client, and proposal objective
- chunking and indexing into `FAISS`
- retrieval of relevant historical content and selection of a reference proposal deck
- slide-by-slide proposal generation using the RFP and retrieved evidence
- Evaluation Dashboard (Faithfulness, Relevance, Completeness metrics)
- Feedback Mechanism (Rating and Feedback persistence)
- local model execution through Ollama (integrated via Docker Compose)

### 5.2 Out of Scope
- exact visual cloning of reference PPT layouts and styles
- multi-user authentication and access management
- workflow approvals or enterprise version control
- enterprise repository connectors such as SharePoint or S3

## 6. User Personas

### 6.1 Primary Persona: Proposal Consultant
- **Needs**: Quick first draft, reusable proposal structure, editability, and ability to leave quality feedback when AI misses the mark.

### 6.2 Secondary Persona: Proposal Manager
- **Needs**: Consistent deck flow, identified risks, traceability of citations, and visibility into proposal metrics/evaluations.

## 7. User Stories

### 7.1 Core User Stories
- As a consultant, I want to upload an RFP so that I can generate a proposal draft without starting from a blank deck.
- As a consultant, I want the tool to reuse a similar proposal template structure so that the output has a coherent storyline.
- As a proposal manager, I want retrieved evidence and citations so that I can validate where the content came from.
- **New**: As a consultant, I want to see an Evaluation Dashboard measuring output Faithfulness and Relevance so I trust the draft.
- **New**: As a consultant, I want to leave a Thumb Up/Down rating and a comment so the AI can be improved in future releases.
- As an enterprise admin, I want to spin up the application via Docker Compose so I do not have to manually configure environments.

## 8. Functional Requirements

### 8.1 RFP Upload and Input Capture
`FR-001` The system shall allow users to upload an RFP document in `PDF`, `DOCX`, or `TXT` format.
`FR-002` The system shall capture metadata including country, sector, domain, client, proposal objective, and assistant prompt overrides.

### 8.2 Historical Content Ingestion
`FR-003` The system shall extract text and chunk it into a `FAISS` vector database.
`FR-004` The system shall index PowerPoint files at slide level to preserve sequence.

### 8.3 Retrieval and Template Selection
`FR-005` The system shall retrieve the top relevant knowledge chunks for the current RFP.
`FR-006` The system shall identify the most relevant reference proposal deck to reconstruct a slide outline.

### 8.4 Evaluation & Feedback (New)
`FR-007` The system shall compute Basic Evaluation Metrics including Faithfulness, Relevance, and Completeness upon generation completion.
`FR-008` The system shall provide UI controls for users to rate the generation (Positive/Negative) and provide free-text feedback.
`FR-009` The system shall store this feedback in a persistent local registry (`data/feedback/`).

### 8.5 Proposal Generation
`FR-010` The system shall generate slide content in the sequence of the selected template deck.
`FR-011` The system shall use the RFP as the primary content source and retrieved content as supporting context.
`FR-012` The system shall generate slide content per slide rather than a monolithic call.

### 8.6 Output Generation
`FR-013` The system shall generate a PowerPoint `.pptx` draft.
`FR-014` The system shall paginate long content into continuation slides.

### 8.7 Containerization (New)
`FR-015` The system shall be executable via `docker-compose up -d --build`.
`FR-016` The container shall persist `data/` volume mounts to the host machine.

## 9. Non-Functional Requirements

### 9.1 Performance
`NFR-001` The system should support local retrieval latency appropriate for desktop execution.

### 9.2 Security and Privacy
`NFR-002` Local model execution through Ollama shall reduce external data exposure. Docker network config shall rely on `host.docker.internal` to hit host APIs without exposing external ports.

### 9.3 Maintainability
`NFR-003` The application shall follow a modular package structure separating `src/services`, `src/graph`, `src/schemas`, and `core/`.

## 10. Product Workflow Specification

1. Upload RFP and metadata.
2. Summarize RFP and derive retrieval query.
3. Retrieve relevant historical chunks and select template deck.
4. Analyze gaps and risks.
5. Generate slide content one slide at a time.
6. Build the final PowerPoint.
7. Compute output Quality Metrics.
8. User evaluates dashboard and provides human-in-the-loop feedback.

## 11. Release Roadmap

### Phase 1: Current MVP
- local UI
- FAISS indexing
- LangGraph workflow
- Ollama integration
- RFP-to-PPT generation
- **Evaluation & Feedback dashboards**
- **Dockerized container environment**

### Phase 2: Product Hardening
- explicit template deck selection
- automated prompt optimization pulling from negative feedback themes
- parsed RFP preview
- richer slide layouts

### Phase 3: Enterprise Readiness
- repository connectors
- multi-user workflow
- template-style reuse
