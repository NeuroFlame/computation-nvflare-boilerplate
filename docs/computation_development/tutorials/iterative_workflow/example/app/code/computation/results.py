from .types import Model


def build_outputs(model: Model):
    return {
        "model.json": {
            "value": model.value,
            "previous_value": model.previous_value,
        }
    }
