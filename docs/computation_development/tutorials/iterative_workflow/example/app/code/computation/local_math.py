from .types import LocalData, Model, SiteUpdate


def compute_local_update(model: Model, state: LocalData) -> SiteUpdate:
    local_mean = sum(state.observations) / len(state.observations)
    return SiteUpdate(estimate=(model.value + local_mean) / 2)
