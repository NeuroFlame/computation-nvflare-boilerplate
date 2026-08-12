"""Aggregate site summaries for the Hello World computation."""

from typing import Dict

from .types import GlobalAverageSummary, LocalAverageSummary


def compute_global_average(
    site_results: Dict[str, LocalAverageSummary],
    decimal_places: int = 2,
) -> GlobalAverageSummary:
    """Compute a weighted global average from all site summaries."""
    total_count = sum(result.count for result in site_results.values())
    if total_count == 0:
        return GlobalAverageSummary(global_average=0.0)

    weighted_sum = sum(
        result.average * result.count for result in site_results.values()
    )
    return GlobalAverageSummary(
        global_average=round(weighted_sum / total_count, decimal_places)
    )
