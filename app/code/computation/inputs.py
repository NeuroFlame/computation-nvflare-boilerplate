"""Load site-local inputs for the example computation."""

import json
import os

from .types import ExampleInputs


def load_inputs(data_dir: str) -> ExampleInputs:
    """Load numeric values from the site's JSON input file."""
    data_file_filepath = os.path.join(data_dir, "data.json")
    with open(data_file_filepath, "r", encoding="utf-8") as data_file:
        values = json.load(data_file)
    return ExampleInputs(values=values)
