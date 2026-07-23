from dataclasses import dataclass

import numpy as np


@dataclass
class RegressionInputs:
    design_matrix: np.ndarray
    response: np.ndarray


@dataclass
class LocalRegressionStatistics:
    xtx: np.ndarray
    xty: np.ndarray
    n_rows: int


@dataclass
class GlobalRegressionModel:
    coefficients: np.ndarray
    n_rows: int
