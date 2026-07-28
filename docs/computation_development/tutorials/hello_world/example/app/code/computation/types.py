"""Define values exchanged by the Hello World computation."""

from dataclasses import dataclass
from typing import List


@dataclass
class ExampleInputs:
    """Site-local numeric inputs."""

    values: List[float]


@dataclass
class LocalAverageSummary:
    """Average and sample count computed by one site."""

    average: float
    count: int


@dataclass
class GlobalAverageSummary:
    """Weighted average computed from all participating sites."""

    global_average: float
