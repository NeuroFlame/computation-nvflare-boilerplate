"""Define final outputs for the Hello World computation."""

from .types import GlobalAverageSummary


def build_final_outputs(global_summary: GlobalAverageSummary):
    """Return the global summary as a JSON output."""
    return {"results.json": global_summary}
