# Basic Regression Tutorial

This tutorial shows how to structure a simple stepped regression computation
using the same author-facing model as the boilerplate.

This is not the full ridge regression implementation. The point is to show the
shape of a real computation without dragging in all of ridge's details.

## Goal

We want a computation that:

- loads tabular site-local data
- computes local sufficient statistics
- aggregates a global regression model
- writes the final model coefficients at each site

Conceptually, each site has rows like:

```text
y, x1, x2, ...
```

and we want a global linear model.

## Recommended Workflow Shape

Use `stepped_workflow(...)` and declare only the computation functions.

For a basic closed-form regression, a good first shape is one local/remote
exchange followed by site output:

1. local sites compute sufficient statistics
2. server aggregates coefficients and sends them back
3. local sites write outputs

In `spec.py`, that looks like:

```python
SPEC = ComputationSpec(
    workflow=stepped_workflow(
        local_step(fn=compute_local_statistics, input_fn=load_regression_inputs),
        remote_step(fn=aggregate_global_regression),
        site_output_step(fn=build_outputs),
    ),
)
```

The framework supplies the aggregator, local data/output paths, parameters
path, logger, serialization, and output writer. Those runtime concerns are not
options on `ComputationSpec`; its normal author input is only the workflow.
Advanced computations may additionally configure custom inline `codecs` or the
`max_inline_array_bytes` safety limit.

Any input or step function can request `logger` by that exact parameter name.
It receives a configured standard Python logger automatically; no logger
factory or lifecycle code belongs in the computation.

## File Responsibilities

Keep the same computation layout:

- `types.py`
  Define typed inputs and results.
- `inputs.py`
  Read site-local regression data.
- `local_math.py`
  Compute local regression statistics.
- `remote_math.py`
  Aggregate the global model.
- `results.py`
  Shape the final output files.

## Suggested Types

Your exact types will vary, but a basic regression might define:

```python
@dataclass
class RegressionInputs:
    X: pd.DataFrame
    y: pd.DataFrame


@dataclass
class LocalRegressionStatistics:
    xtx: list
    xty: list
    n_rows: int


@dataclass
class GlobalRegressionModel:
    coefficients: list
    n_rows: int
```

These are ordinary dataclasses. DataFrame fields are handled automatically; do
not add framework codec imports or `field(metadata=...)` declarations.

The key idea is:

- authors define computation-specific types
- the framework handles orchestration

## Local Math

In `local_math.py`, keep the math focused.

For a basic regression, the local site might compute:

- `X^T X`
- `X^T y`
- row count

Example shape:

```python
def compute_local_statistics(inputs: RegressionInputs) -> LocalRegressionStatistics:
    xtx = inputs.X.T @ inputs.X
    xty = inputs.X.T @ inputs.y
    return LocalRegressionStatistics(
        xtx=xtx.values.tolist(),
        xty=xty.values.tolist(),
        n_rows=len(inputs.X),
    )
```

The important point is that this file should contain math, not framework logic.

## Remote Math

In `remote_math.py`, the server aggregates all local statistics:

- sum `X^T X`
- sum `X^T y`
- solve for coefficients

Example shape:

```python
from typing import Dict


def aggregate_global_regression(
    site_results: Dict[str, LocalRegressionStatistics],
) -> GlobalRegressionModel:
    xtx_sum = sum(np.array(result.xtx) for result in site_results.values())
    xty_sum = sum(np.array(result.xty) for result in site_results.values())
    coefficients = np.linalg.solve(xtx_sum, xty_sum)
    return GlobalRegressionModel(
        coefficients=coefficients.tolist(),
        n_rows=sum(result.n_rows for result in site_results.values()),
    )
```

The dictionary keys are site display names, so result storage is independent of
arrival order. The `LocalRegressionStatistics` value annotation is what tells
the framework to reconstruct each site's dataclass. Use `List[...]` only when
site identity is intentionally irrelevant.

Again, this should stay focused on aggregation math.

## Outputs

In `results.py`, return the final output shape you want written to disk.

Example:

```python
def build_outputs(global_model: GlobalRegressionModel):
    return {
        "global_regression.json": {
            "coefficients": global_model.coefficients,
            "n_rows": global_model.n_rows,
        }
    }
```

The keys are the output filenames. JSON values are serialized automatically;
DataFrames can be returned under `.csv` or `.tsv` filenames, and strings under
`.html`, `.md`, or `.txt` filenames. For a specialized format, request
`output_dir`, write it directly, and return `None`.

## Why This Matters

This structure keeps the author mental model simple:

1. get inputs
2. run local math
3. aggregate remotely
4. return outputs

instead of:

1. write a controller
2. write an executor
3. manage `Shareable`
4. manage framework state manually

## Where To Go Next

Use this tutorial as the template for basic stepped tabular computations.

For more complex regression flows, such as ridge with multiple rounds of global
parameters and local metrics, follow the same layout but add more steps to the
workflow rather than breaking the author-facing structure.

When the same update pair repeats until convergence, use the
[Iterative Workflow Tutorial](./tutorial_iterative_workflow.md) instead of
manually declaring rounds.
