from .types import GlobalAverageSummary


def build_final_outputs(global_summary: GlobalAverageSummary):
    return {"results.json": global_summary}
