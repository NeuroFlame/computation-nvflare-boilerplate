from framework import (
    ComputationSpec,
    local_step,
    remote_step,
    site_output_step,
    stepped_workflow,
)

from .inputs import load_inputs
from .local_math import compute_local_average
from .remote_math import compute_global_average
from .results import build_final_outputs


SPEC = ComputationSpec(
    workflow=stepped_workflow(
        local_step(fn=compute_local_average, input_fn=load_inputs),
        remote_step(fn=compute_global_average),
        site_output_step(fn=build_final_outputs),
    ),
)
