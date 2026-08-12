"""Define final outputs for the regression computation."""

from .types import GlobalRegressionModel


def build_outputs(global_model: GlobalRegressionModel):
    """Return readable global coefficients as a JSON output."""
    return {
        "global_regression.json": {
            "intercept": round(float(global_model.coefficients[0]), 12),
            "slope": round(float(global_model.coefficients[1]), 12),
            "n_rows": global_model.n_rows,
        }
    }
