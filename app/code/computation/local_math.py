from .types import ExampleInputs, LocalAverageSummary


def compute_local_average(inputs: ExampleInputs, decimal_places: int = 2) -> LocalAverageSummary:
    """
    Calculate the average and count from a list of numbers.

    :param inputs: Loaded computation inputs.
    :param decimal_places: Number of decimal places to round the average.
    :return: The local average summary.
    """
    if not inputs.values:
        return LocalAverageSummary(average=0.0, count=0)

    total_sum = sum(inputs.values)
    total_count = len(inputs.values)

    average = round(total_sum / total_count, decimal_places)
    return LocalAverageSummary(average=average, count=total_count)
