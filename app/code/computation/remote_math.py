from typing import Dict

from .types import GlobalAverageSummary, LocalAverageSummary


def compute_global_average(local_results: Dict[str, LocalAverageSummary], decimal_places: int = 2) -> GlobalAverageSummary:
    """Return the weighted global average from local site summaries."""
    if not local_results:
        return GlobalAverageSummary(global_average=0)

    weighted_sum = sum(item.average * item.count for item in local_results.values())
    total_count = sum(item.count for item in local_results.values())

    if total_count == 0:
        return GlobalAverageSummary(global_average=0)

    global_average = round(weighted_sum / total_count, decimal_places)

    return GlobalAverageSummary(global_average=global_average)
