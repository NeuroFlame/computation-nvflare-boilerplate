"""Define values exchanged by the regression computation."""

from dataclasses import dataclass

import numpy as np


@dataclass
class RegressionInputs:
    """Site-local design matrix and response vector."""

    design_matrix: np.ndarray
    response: np.ndarray


@dataclass
class LocalRegressionStatistics:
    """Sufficient statistics computed from one site's rows."""

    xtx: np.ndarray
    xty: np.ndarray
    n_rows: int


@dataclass
class GlobalRegressionModel:
    """Global coefficients and contributing row count."""

    coefficients: np.ndarray
    n_rows: int
