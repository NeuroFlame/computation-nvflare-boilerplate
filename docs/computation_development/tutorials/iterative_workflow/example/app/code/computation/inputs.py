"""Load the initial model and persistent site data."""

import json
import os

from framework import with_state

from .types import LocalData, Model


def load_initial_model(data_dir: str):
    """Return the initial model with site observations as persistent state."""
    with open(os.path.join(data_dir, "data.json"), encoding="utf-8") as data_file:
        observations = json.load(data_file)

    return with_state(
        Model(value=0.0),
        LocalData(observations=observations),
    )
