"""Define payload and state values used by the iterative workflow."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Model:
    """Global model exchanged between the server and sites."""

    value: float
    previous_value: Optional[float] = None


@dataclass
class LocalData:
    """Observations cached persistently at one site."""

    observations: List[float]


@dataclass
class SiteUpdate:
    """One site's estimate for the next global model."""

    estimate: float


@dataclass
class RemoteState:
    """Previous global value cached persistently on the server."""

    value: float
