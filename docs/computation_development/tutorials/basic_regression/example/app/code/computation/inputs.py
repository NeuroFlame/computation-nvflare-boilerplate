"""Load site-local tabular regression inputs."""

import os

import numpy as np
import pandas as pd

from .types import RegressionInputs


def load_regression_inputs(data_dir: str) -> RegressionInputs:
    """Load a CSV table and construct its regression arrays."""
    table = pd.read_csv(os.path.join(data_dir, "regression.csv"))
    design_matrix = np.column_stack(
        [
            np.ones(len(table)),
            table["x"].to_numpy(dtype=float),
        ]
    )
    return RegressionInputs(
        design_matrix=design_matrix,
        response=table["y"].to_numpy(dtype=float),
    )
