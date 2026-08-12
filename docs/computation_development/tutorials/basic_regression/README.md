# Basic Regression Tutorial

This tutorial replaces Hello World with a complete federated linear regression.
It uses the same author-facing workflow:

1. each site loads its own rows
2. each site computes `X^T X` and `X^T y`
3. the server sums those statistics and solves for global coefficients
4. every site writes the global model

The raw rows never leave their site. A complete copy of the finished example is
in [`example/`](./example/).

## 1. Define The Values

Create `app/code/computation/types.py`:

```python
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
```

NumPy arrays are standard framework values. Authors do not need to write
payload conversion methods or register a codec for bounded arrays.

## 2. Load A Site's Table

Create `app/code/computation/inputs.py`:

```python
"""Load site-local tabular regression inputs."""

import os

import numpy as np
import pandas as pd

from .types import RegressionInputs


def load_regression_inputs(data_dir: str) -> RegressionInputs:
    """Load a CSV table and construct its regression arrays."""
    table = pd.read_csv(os.path.join(data_dir, "regression.csv"))
    design_matrix = np.column_stack(
        [
            np.ones(len(table)),
            table["x"].to_numpy(dtype=float),
        ]
    )
    return RegressionInputs(
        design_matrix=design_matrix,
        response=table["y"].to_numpy(dtype=float),
    )
```

The first design-matrix column is the intercept. The second contains the single
predictor `x`.

## 3. Compute Local Statistics

Create `app/code/computation/local_math.py`:

```python
"""Compute site-local regression statistics."""

from .types import LocalRegressionStatistics, RegressionInputs


def compute_local_statistics(
    inputs: RegressionInputs,
) -> LocalRegressionStatistics:
    """Compute one site's sufficient statistics."""
    return LocalRegressionStatistics(
        xtx=inputs.design_matrix.T @ inputs.design_matrix,
        xty=inputs.design_matrix.T @ inputs.response,
        n_rows=len(inputs.response),
    )
```

This function contains only local math. Its result is small enough to transport
while the original subject rows remain local.

## 4. Fit The Global Model

Create `app/code/computation/remote_math.py`:

```python
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
```

The value annotation in `Dict[str, LocalRegressionStatistics]` tells the
framework how to reconstruct every site's dataclass. `ridge_penalty` comes from
the computation parameters when provided.

The intercept is not penalized. A value of `0.0` produces ordinary least
squares.

## 5. Produce Plain JSON

Create `app/code/computation/results.py`:

```python
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
```

The output function turns the coefficient array into a small, readable report.
The framework writes it under each site's output directory.

## 6. Declare The Workflow

Create `app/code/computation/spec.py`:

```python
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
```

The computation author does not define controllers, executors, aggregators,
task names, transport payloads, or file writers.

## 7. Add Site Tables

Create `test_data/site1/regression.csv`:

```csv
x,y
0,1
1,3
2,5
```

Create `test_data/site2/regression.csv`:

```csv
x,y
3,7
4,9
5,11
```

Create `test_data/server/parameters.json`:

```json
{
  "ridge_penalty": 0.0
}
```

Both sites follow `y = 1 + 2x`, so the expected global intercept is `1` and the
expected slope is `2`.

## 8. Run It

Install and run the example from the repository root:

```bash
cp docs/computation_development/tutorials/basic_regression/example/app/code/computation/*.py app/code/computation/
cp docs/computation_development/tutorials/basic_regression/example/test_data/site1/regression.csv test_data/site1/regression.csv
cp docs/computation_development/tutorials/basic_regression/example/test_data/site2/regression.csv test_data/site2/regression.csv
cp docs/computation_development/tutorials/basic_regression/example/test_data/server/parameters.json test_data/server/parameters.json
./run_local_simulation.sh site1,site2
```

Both sites receive
`test_output/simulate_job/<site>/global_regression.json`:

```json
{
  "intercept": 1.0,
  "slope": 2.0,
  "n_rows": 6
}
```

## 9. Change The Model

Change `ridge_penalty` to `1.0` and rerun. Only
`test_data/server/parameters.json` changes; the workflow remains the same. The
slope is then shrunk toward zero:

```json
{
  "intercept": 1.27027027027,
  "slope": 1.891891891892,
  "n_rows": 6
}
```

## What Moved

| Value | From | To |
| --- | --- | --- |
| Subject rows | Site input file | Local loader only |
| `X^T X`, `X^T y`, row count | Site math | Server |
| Global coefficients | Server math | Every site's output step |

For a repeated local/server update, continue with the
[Iterative Workflow Tutorial](../iterative_workflow/).
