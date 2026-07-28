"""Declare the iterative computation workflow."""

from framework import (
    ComputationSpec,
    iterative_workflow,
    local_step,
    remote_step,
    site_output_step,
)

from .inputs import load_initial_model
from .local_math import compute_local_update
from .remote_math import compute_global_update, has_converged
from .results import build_outputs

SPEC = ComputationSpec(
    workflow=iterative_workflow(
        local_step(fn=compute_local_update, input_fn=load_initial_model),
        remote_step(fn=compute_global_update),
        site_output_step(fn=build_outputs),
        stop_when=has_converged,
        max_iterations=50,
    ),
)
