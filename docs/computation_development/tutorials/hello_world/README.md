# Hello World Tutorial

This tutorial builds a complete computation that:

1. reads numbers stored at each site
2. computes each site's average and count
3. computes a weighted global average on the server
4. writes the same global result at every site

Only files under `app/code/computation/` contain computation logic. A complete
copy of the finished example is in [`example/`](./example/).

## 1. Define The Values

Create `app/code/computation/types.py`:

```python
"""Define values exchanged by the Hello World computation."""

from dataclasses import dataclass
from typing import List


@dataclass
class ExampleInputs:
    """Site-local numeric inputs."""

    values: List[float]


@dataclass
class LocalAverageSummary:
    """Average and sample count computed by one site."""

    average: float
    count: int


@dataclass
class GlobalAverageSummary:
    """Weighted average computed from all participating sites."""

    global_average: float
```

These are ordinary Python dataclasses. They contain computation data, not
NVFlare objects or serialization methods.

## 2. Load Site Data

Create `app/code/computation/inputs.py`:

```python
"""Load site-local inputs for the Hello World computation."""

import json
import os

from .types import ExampleInputs


def load_inputs(data_dir: str) -> ExampleInputs:
    """Load numeric values from the site's JSON input file."""
    with open(os.path.join(data_dir, "data.json"), encoding="utf-8") as data_file:
        return ExampleInputs(values=json.load(data_file))
```

The framework supplies `data_dir` because the function requests that exact
parameter name. On each site it points to that site's input directory.

## 3. Write Local Math

Create `app/code/computation/local_math.py`:

```python
"""Compute site-local summaries for the Hello World computation."""

from .types import ExampleInputs, LocalAverageSummary


def compute_local_average(
    inputs: ExampleInputs,
    decimal_places: int = 2,
) -> LocalAverageSummary:
    """Compute one site's rounded average and sample count."""
    if not inputs.values:
        return LocalAverageSummary(average=0.0, count=0)

    return LocalAverageSummary(
        average=round(sum(inputs.values) / len(inputs.values), decimal_places),
        count=len(inputs.values),
    )
```

`inputs` receives the value returned by `load_inputs`. `decimal_places` is read
from the computation parameters when present and otherwise uses its Python
default.

## 4. Write Server Math

Create `app/code/computation/remote_math.py`:

```python
"""Aggregate site summaries for the Hello World computation."""

from typing import Dict

from .types import GlobalAverageSummary, LocalAverageSummary


def compute_global_average(
    site_results: Dict[str, LocalAverageSummary],
    decimal_places: int = 2,
) -> GlobalAverageSummary:
    """Compute a weighted global average from all site summaries."""
    total_count = sum(result.count for result in site_results.values())
    if total_count == 0:
        return GlobalAverageSummary(global_average=0.0)

    weighted_sum = sum(
        result.average * result.count for result in site_results.values()
    )
    return GlobalAverageSummary(
        global_average=round(weighted_sum / total_count, decimal_places)
    )
```

The server receives one `LocalAverageSummary` per site. Dictionary keys are site
display names, so arrival order does not affect the computation.

## 5. Choose Output Files

Create `app/code/computation/results.py`:

```python
"""Define final outputs for the Hello World computation."""

from .types import GlobalAverageSummary


def build_final_outputs(global_summary: GlobalAverageSummary):
    """Return the global summary as a JSON output."""
    return {"results.json": global_summary}
```

The returned key is a relative output filename. The framework serializes the
dataclass and writes the JSON file.

## 6. Declare The Workflow

Create `app/code/computation/spec.py`:

```python
"""Declare the Hello World computation workflow."""

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
```

This is the complete orchestration definition. The three functions execute at:

| Function | Location | Receives |
| --- | --- | --- |
| `compute_local_average` | Every site | That site's loaded input |
| `compute_global_average` | Server | Results keyed by site name |
| `build_final_outputs` | Every site | The server's global result |

## 7. Add Test Data

Create `test_data/site1/data.json`:

```json
[2, 4, 6]
```

Create `test_data/site2/data.json`:

```json
[10, 14]
```

Create `test_data/server/parameters.json`:

```json
{
  "decimal_places": 2
}
```

## 8. Run It

The example files can be installed from the repository root:

```bash
cp docs/computation_development/tutorials/hello_world/example/app/code/computation/*.py app/code/computation/
cp docs/computation_development/tutorials/hello_world/example/test_data/site1/data.json test_data/site1/data.json
cp docs/computation_development/tutorials/hello_world/example/test_data/site2/data.json test_data/site2/data.json
cp docs/computation_development/tutorials/hello_world/example/test_data/server/parameters.json test_data/server/parameters.json
./run_local_simulation.sh site1,site2
```

Both sites receive `test_output/simulate_job/<site>/results.json`:

```json
{
  "global_average": 7.2
}
```

The calculation is:

```text
site1: average=4,  count=3
site2: average=12, count=2
global: ((4 * 3) + (12 * 2)) / 5 = 7.2
```

## 9. Change A Parameter

Set `decimal_places` to `0` in `test_data/server/parameters.json` and run again.
The output becomes:

```json
{
  "global_average": 7.0
}
```

No workflow or runtime code changes are required.

## Next

Continue with the [Basic Regression Tutorial](../basic_regression/).
