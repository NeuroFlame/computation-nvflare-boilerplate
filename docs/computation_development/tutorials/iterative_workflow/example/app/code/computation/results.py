"""Define final outputs for the iterative computation."""

from .types import Model


def build_outputs(model: Model):
    """Return the final and previous model values as JSON."""
    return {
        "model.json": {
            "value": model.value,
            "previous_value": model.previous_value,
        }
    }
