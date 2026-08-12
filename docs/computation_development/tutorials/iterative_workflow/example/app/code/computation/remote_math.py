"""Aggregate iterative site updates and determine convergence."""

from typing import Dict, Optional

from framework import with_state

from .types import Model, RemoteState, SiteUpdate


def compute_global_update(
    site_updates: Dict[str, SiteUpdate],
    state: Optional[RemoteState] = None,
):
    """Average site estimates and retain the previous server value."""
    value = sum(update.estimate for update in site_updates.values()) / len(site_updates)
    previous_value = None if state is None else state.value
    return with_state(
        Model(value=value, previous_value=previous_value),
        RemoteState(value=value),
    )


def has_converged(model: Model, tolerance: float = 0.01) -> bool:
    """Return whether the global model changed within tolerance."""
    if model.previous_value is None:
        return False
    return abs(model.value - model.previous_value) <= tolerance
