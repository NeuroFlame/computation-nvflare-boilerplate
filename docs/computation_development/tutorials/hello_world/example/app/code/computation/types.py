from dataclasses import dataclass
from typing import List


@dataclass
class ExampleInputs:
    values: List[float]


@dataclass
class LocalAverageSummary:
    average: float
    count: int


@dataclass
class GlobalAverageSummary:
    global_average: float
