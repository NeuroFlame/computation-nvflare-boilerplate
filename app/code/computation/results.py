from .types import GlobalAverageSummary, LocalAverageSummary


def build_local_outputs(local_summary: LocalAverageSummary):
    return {"results.json": local_summary}


def build_final_outputs(global_summary: GlobalAverageSummary):
    return {"results.json": global_summary}
