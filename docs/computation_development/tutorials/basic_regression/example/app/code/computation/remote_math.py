"""Fit a global model from site regression statistics."""

from typing import Dict

import numpy as np

from .types import GlobalRegressionModel, LocalRegressionStatistics


def aggregate_global_regression(
    site_results: Dict[str, LocalRegressionStatistics],
    ridge_penalty: float = 0.0,
) -> GlobalRegressionModel:
    """Sum sufficient statistics and solve for global coefficients."""
    xtx = sum((result.xtx for result in site_results.values()), start=np.zeros((2, 2)))
    xty = sum((result.xty for result in site_results.values()), start=np.zeros(2))

    penalty = np.eye(2) * ridge_penalty
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(xtx + penalty, xty)

    return GlobalRegressionModel(
        coefficients=coefficients,
        n_rows=sum(result.n_rows for result in site_results.values()),
    )
