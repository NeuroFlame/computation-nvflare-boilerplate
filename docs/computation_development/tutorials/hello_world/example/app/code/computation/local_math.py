from .types import ExampleInputs, LocalAverageSummary


def compute_local_average(
    inputs: ExampleInputs,
    decimal_places: int = 2,
) -> LocalAverageSummary:
    if not inputs.values:
        return LocalAverageSummary(average=0.0, count=0)

    return LocalAverageSummary(
        average=round(sum(inputs.values) / len(inputs.values), decimal_places),
        count=len(inputs.values),
    )
