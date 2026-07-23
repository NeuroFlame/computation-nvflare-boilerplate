import json
import os

from .types import ExampleInputs


def load_inputs(data_dir: str) -> ExampleInputs:
    with open(os.path.join(data_dir, "data.json"), encoding="utf-8") as data_file:
        return ExampleInputs(values=json.load(data_file))
