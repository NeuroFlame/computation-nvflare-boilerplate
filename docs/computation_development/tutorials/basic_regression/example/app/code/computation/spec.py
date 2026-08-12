"""Declare the basic regression computation workflow."""

from framework import (
    ComputationSpec,
    local_step,
    remote_step,
    site_output_step,
    stepped_workflow,
)

from .inputs import load_regression_inputs
from .local_math import compute_local_statistics
from .remote_math import aggregate_global_regression
from .results import build_outputs

SPEC = ComputationSpec(
    workflow=stepped_workflow(
        local_step(fn=compute_local_statistics, input_fn=load_regression_inputs),
        remote_step(fn=aggregate_global_regression),
        site_output_step(fn=build_outputs),
    ),
)
