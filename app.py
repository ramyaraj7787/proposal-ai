# ==========================================================
# 🧠 AI Proposal Generation Tool — Production Streamlit UI
# ==========================================================

import sys
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------
# Path Setup (for local package imports)
# ---------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------
from core.config import get_settings # added this import so Pylance stops complaining
from core.constants import APP_NAME, DEFAULT_PROPOSAL_PROMPT
from core.logger import get_logger
from graph.builder import build_proposal_graph
from schemas.state_schema import ProposalInput
from graph.state import ProposalState
from services.ingestion.preprocess import build_rfp_preview, save_uploaded_file
from services.evaluation.metrics import compute_basic_metrics
from services.evaluation.feedback_store import save_feedback, load_feedback
from services.generation.prompt_optimizer import build_feedback_summary

logger = get_logger(__name__)

# ---------------------------------------------------------
# Cached Resources (IMPORTANT for performance)
# ---------------------------------------------------------
@st.cache_resource
def load_graph(settings):
    return build_proposal_graph(settings)


@st.cache_resource
def load_settings():
    return get_settings()


# ---------------------------------------------------------
# Utility UI Components
# ---------------------------------------------------------
def render_header():
    st.title(APP_NAME)
    st.markdown(
        "### 🚀 AI-Powered Proposal Generator\n"
        "Generate high-quality proposal drafts grounded in historical data and RFP context."
    )


def render_sidebar():
    with st.sidebar:
        st.header("⚙️ Configuration")

        return {
            "country": st.text_input("Country", "India"),
            "sector": st.text_input("Sector", "Financial Services"),
            "domain": st.text_input("Domain", "Data & AI"),
            "client": st.text_input("Client", "Confidential Client"),
            "proposal_objective": st.text_area(
                "Proposal Objective",
                "Build an AI-led transformation proposal aligned to the RFP.",
            ),
            "assistant_prompt": st.text_area(
                "LLM Prompt Override",
                DEFAULT_PROPOSAL_PROMPT,
            ),
            "debug_mode": st.checkbox("Enable Debug Mode"),
        }


def render_file_upload():
    return st.file_uploader(
        "📄 Upload RFP (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
    )


def show_progress(progress_bar, step, message):
    progress_bar.progress(step)
    st.caption(message)


# ---------------------------------------------------------
# Main Application
# ---------------------------------------------------------
def main():
    settings = load_settings()
    graph = load_graph(settings)

    st.set_page_config(page_title="AI Proposal Tool", layout="wide")

    render_header()
    config = render_sidebar()

    upload = render_file_upload()

    # -----------------------------------------------------
    # Preview Section
    # -----------------------------------------------------
    if upload:
        preview_path = save_uploaded_file(upload, settings.output_dir / "uploads")

        with st.expander("🔍 RFP Preview", expanded=False):
            st.text(build_rfp_preview(str(preview_path)))

    # -----------------------------------------------------
    # Execution
    # -----------------------------------------------------
    if st.button("🚀 Generate Proposal", disabled=upload is None) and upload is not None:

        progress_bar = st.progress(0)
        status = st.empty()

        try:
            # Step 1: Save file
            status.info("Saving uploaded file...")
            saved_rfp = save_uploaded_file(upload, settings.output_dir / "uploads")
            show_progress(progress_bar, 10, "File saved")

            # Step 2: Prepare state
            status.info("Preparing pipeline input...")
            proposal_input = ProposalInput(
                rfp_path=str(saved_rfp),
                **config
            )
            initial_state = ProposalState(**proposal_input.model_dump())
            show_progress(progress_bar, 20, "Input prepared")

            # Step 3: Run pipeline
            status.info("Running AI pipeline (this may take a few seconds)...")
            start_time = time.time()
            logger.info("Starting proposal generation for: %s", saved_rfp)

            result = graph.invoke(initial_state)

            duration = round(time.time() - start_time, 2)
            logger.info("Proposal generation completed in %ss", duration)
            show_progress(progress_bar, 90, f"Pipeline completed in {duration}s")

            # Step 4: Display outputs
            status.success("✅ Proposal generated successfully!")
            progress_bar.progress(100)

            st.session_state.proposal_result = result

        except Exception as e:
            logger.error("Proposal generation failed: %s", e, exc_info=True)
            st.error(f"❌ Error occurred: {str(e)}")

    if "proposal_result" in st.session_state:
        render_results(st.session_state.proposal_result, config["debug_mode"])

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------
    st.markdown("---")
    st.caption("AI Proposal Tool • Production UI")


# ---------------------------------------------------------
# Results Rendering
# ---------------------------------------------------------
def render_results(result, debug=False):

    tabs = st.tabs([
        "📌 Summary",
        "⚠️ Risks",
        "📚 Evidence",
        "💡 Improvements",
        "📄 Sections",
        "📥 Output",
        "📊 Evaluation",
        "📝 Feedback",
        "🛠 Debug" if debug else "ℹ️ Info",
    ])

    # Summary
    with tabs[0]:
        st.subheader("Executive Summary")
        st.write(result.get("executive_summary", ""))

    # Risks
    with tabs[1]:
        st.subheader("Risks & Gaps")
        for item in result.get("gap_analysis", []):
            st.write(f"- {item}")

    # Evidence
    with tabs[2]:
        st.subheader("Retrieved Evidence")
        for item in result.get("citations", []):
            st.write(f"- {item}")

    # Improvements
    with tabs[3]:
        st.subheader("AI Recommendations")
        for item in result.get("improvement_recommendations", []):
            st.write(f"- {item}")

    # Sections
    with tabs[4]:
        st.subheader("Generated Sections")
        for section in result.get("proposal_sections", []):
            with st.expander(section["title"]):
                st.write(section["content"])

    # Output
    with tabs[5]:
        ppt_path = Path(result["ppt_output_path"])
        st.success(f"Generated: {ppt_path}")

        with open(ppt_path, "rb") as f:
            st.download_button(
                label="⬇️ Download PPT",
                data=f,
                file_name=ppt_path.name,
            )
            
    # Evaluation     
    with tabs[6]:
        st.subheader("📊 Evaluation Dashboard")

        metrics = compute_basic_metrics(result)

        # KPI Cards
        col1, col2, col3 = st.columns(3)

        col1.metric("Faithfulness", metrics["faithfulness"])
        col2.metric("Relevance", metrics["relevance"])
        col3.metric("Completeness", metrics["completeness"])

        st.markdown("---")

        # System Metrics
        col4, col5 = st.columns(2)
        col4.metric("Sections Generated", metrics["sections_count"])
        col5.metric("Retrieved Chunks", metrics["retrieved_chunks"])

        st.markdown("---")

        # Visual Bars
        st.write("### Quality Breakdown")

        st.progress(metrics["faithfulness"])
        st.caption("Faithfulness (Grounding to retrieved context)")

        st.progress(metrics["relevance"])
        st.caption("Relevance to RFP")

        st.progress(metrics["completeness"])
        st.caption("Proposal completeness")

    # Feedback
    with tabs[7]:
        st.subheader("📝 Feedback")
        st.write("Help improve the system by rating this proposal.")
        col1, col2 = st.columns(2)
        with col1:
            thumbs_up = st.button("👍 Good")
        with col2:
            thumbs_down = st.button("👎 Needs Improvement")
        comment = st.text_area("Additional Feedback (optional)")

        if thumbs_up or thumbs_down:
            rating = "positive" if thumbs_up else "negative"

            feedback_data = {
                "rating": rating,
                "comment": comment,
                "rfp_path": result.get("rfp_path"),
                "sections_count": len(result.get("proposal_sections", [])),
                "retrieved_chunks": len(result.get("retrieved_context", [])),
                "quality_score": result.get("quality_score"),
            }

            save_feedback(feedback_data)

            st.success("✅ Feedback recorded. Thank you!")

        # --- Recent Feedback Signals card ---
        st.markdown("---")
        st.subheader("📡 Recent Feedback Signals")
        feedback_history = load_feedback(max_entries=50)
        if not feedback_history:
            st.info("No feedback recorded yet. Your ratings will be used to improve future generations.")
        else:
            summary = build_feedback_summary(feedback_history)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Ratings", summary["total"])
            c2.metric("👍 Positive", summary["positive"])
            c3.metric("👎 Negative", summary["negative"])

            if summary["themes"]:
                st.warning(
                    "**Quality signals detected from comments — these are already being applied to generation:**\n\n"
                    + "\n".join(f"- `{t}`" for t in summary["themes"])
                )
            else:
                st.success("No recurring quality issues detected in feedback comments.")

            with st.expander("📋 Recent Comments", expanded=False):
                for entry in feedback_history[:10]:
                    comment_text = entry.get("comment", "").strip()
                    if comment_text:
                        icon = "👍" if entry.get("rating") == "positive" else "👎"
                        ts = entry.get("timestamp", "")[:10]
                        st.markdown(f"{icon} **{ts}** — {comment_text}")

    # Debug / Info
    with tabs[8]:
        if debug:
            st.subheader("Debug Trace")
            st.json(result)
        else:
            st.info("Enable debug mode to view full pipeline output.")


# ---------------------------------------------------------
# Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    main()