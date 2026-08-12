"""Define output files produced by the example computation."""

from .types import GlobalAverageSummary, LocalAverageSummary


def build_local_outputs(local_summary: LocalAverageSummary):
    """Return the local summary as a JSON output."""
    return {"results.json": local_summary}


def build_final_outputs(global_summary: GlobalAverageSummary):
    """Return the global summary as a JSON output."""
    return {"results.json": global_summary}
