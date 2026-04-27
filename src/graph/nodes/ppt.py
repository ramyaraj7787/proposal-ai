"""PowerPoint export nodes."""

from graph.state import ProposalState
from services.ppt.ppt_builder import build_proposal_ppt


def build_ppt_node(settings):
    """Return the node that exports the final PowerPoint."""

    def ppt_node(state: ProposalState) -> ProposalState:
        state["ppt_output_path"] = build_proposal_ppt(state, settings)
        return state

    return ppt_node
