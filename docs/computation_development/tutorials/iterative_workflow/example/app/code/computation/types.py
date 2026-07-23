from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Model:
    value: float
    previous_value: Optional[float] = None


@dataclass
class LocalData:
    observations: List[float]


@dataclass
class SiteUpdate:
    estimate: float


@dataclass
class RemoteState:
    value: float
