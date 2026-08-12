"""Compute one site update during each iteration."""

from .types import LocalData, Model, SiteUpdate


def compute_local_update(model: Model, state: LocalData) -> SiteUpdate:
    """Move the model halfway toward the site's local mean."""
    local_mean = sum(state.observations) / len(state.observations)
    return SiteUpdate(estimate=(model.value + local_mean) / 2)
