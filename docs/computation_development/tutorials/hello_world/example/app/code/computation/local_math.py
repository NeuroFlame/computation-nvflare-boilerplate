"""Compute site-local summaries for the Hello World computation."""

from .types import ExampleInputs, LocalAverageSummary


def compute_local_average(
    inputs: ExampleInputs,
    decimal_places: int = 2,
) -> LocalAverageSummary:
    """Compute one site's rounded average and sample count."""
    if not inputs.values:
        return LocalAverageSummary(average=0.0, count=0)

    return LocalAverageSummary(
        average=round(sum(inputs.values) / len(inputs.values), decimal_places),
        count=len(inputs.values),
    )
