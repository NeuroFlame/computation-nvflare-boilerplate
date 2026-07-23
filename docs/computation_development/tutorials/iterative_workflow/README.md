# Iterative Workflow Tutorial

This tutorial builds a computation that repeatedly exchanges a model between
sites and the server until it converges.

Each site has a private list of observations. On every iteration:

1. each site moves the current model halfway toward its local mean
2. the server averages the site updates
3. the server checks whether the global value changed by at most the tolerance
4. the process repeats or every site writes the final model

The framework owns the loop, transport, and persistent local/server state. A
complete copy of the finished example is in [`example/`](./example/).

## 1. Define Payload And State Values

Create `app/code/computation/types.py`:

```python
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Model:
    value: float
    previous_value: Optional[float] = None


@dataclass
class LocalData:
    observations: List[float]


@dataclass
class SiteUpdate:
    estimate: float


@dataclass
class RemoteState:
    value: float
```

`Model` travels between server and sites. `LocalData` stays at its site, and
`RemoteState` stays on the server.

## 2. Load Inputs Once

Create `app/code/computation/inputs.py`:

```python
import json
import os

from framework import with_state

from .types import LocalData, Model


def load_initial_model(data_dir: str):
    with open(os.path.join(data_dir, "data.json"), encoding="utf-8") as data_file:
        observations = json.load(data_file)

    return with_state(
        Model(value=0.0),
        LocalData(observations=observations),
    )
```

`with_state(payload, state)` returns two values with different lifetimes:

- `Model(value=0.0)` becomes the first local-step payload.
- `LocalData` is cached at that site and injected into every iteration.

The input function runs only on the first iteration.

## 3. Write The Repeated Local Update

Create `app/code/computation/local_math.py`:

```python
from .types import LocalData, Model, SiteUpdate


def compute_local_update(model: Model, state: LocalData) -> SiteUpdate:
    local_mean = sum(state.observations) / len(state.observations)
    return SiteUpdate(estimate=(model.value + local_mean) / 2)
```

The first argument receives the initial model on iteration one and the previous
server result on later iterations. The exact parameter name `state` requests
the site's cached `LocalData`.

## 4. Combine Updates And Keep Server State

Create `app/code/computation/remote_math.py`:

```python
from typing import Dict, Optional

from framework import with_state

from .types import Model, RemoteState, SiteUpdate


def compute_global_update(
    site_updates: Dict[str, SiteUpdate],
    state: Optional[RemoteState] = None,
):
    value = sum(update.estimate for update in site_updates.values()) / len(
        site_updates
    )
    previous_value = None if state is None else state.value
    return with_state(
        Model(value=value, previous_value=previous_value),
        RemoteState(value=value),
    )


def has_converged(model: Model, tolerance: float = 0.01) -> bool:
    if model.previous_value is None:
        return False
    return abs(model.value - model.previous_value) <= tolerance
```

The remote function's `state` is independent from the local cached state. It is
stored on the server and supplied to the next remote call.

`has_converged` is an ordinary author function. Its name is not special. The
framework calls the function named by `stop_when`.

## 5. Write The Final Model

Create `app/code/computation/results.py`:

```python
from .types import Model


def build_outputs(model: Model):
    return {
        "model.json": {
            "value": model.value,
            "previous_value": model.previous_value,
        }
    }
```

This runs once after convergence or after the iteration cap.

## 6. Declare The Loop

Create `app/code/computation/spec.py`:

```python
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
```

The author supplies one local function, one server function, one output
function, a convergence predicate, and a safety limit. No rounds or task names
are manually declared.

## 7. Add Test Data

Create `test_data/site1/data.json`:

```json
[2, 4, 6]
```

Create `test_data/site2/data.json`:

```json
[8, 10, 12]
```

Create `test_data/server/parameters.json`:

```json
{
  "tolerance": 0.01
}
```

The site means are `4` and `10`. Their global target is `7`.

## 8. Run It

Install and run the example from the repository root:

```bash
cp docs/computation_development/tutorials/iterative_workflow/example/app/code/computation/*.py app/code/computation/
cp docs/computation_development/tutorials/iterative_workflow/example/test_data/site1/data.json test_data/site1/data.json
cp docs/computation_development/tutorials/iterative_workflow/example/test_data/site2/data.json test_data/site2/data.json
cp docs/computation_development/tutorials/iterative_workflow/example/test_data/server/parameters.json test_data/server/parameters.json
./run_local_simulation.sh site1,site2
```

The global value follows:

| Iteration | Global value | Change |
| ---: | ---: | ---: |
| 1 | `3.5` | n/a |
| 2 | `5.25` | `1.75` |
| 3 | `6.125` | `0.875` |
| 9 | `6.986328125` | `0.013671875` |
| 10 | `6.9931640625` | `0.0068359375` |

Iteration 10 satisfies the `0.01` tolerance. Both sites receive
`test_output/simulate_job/<site>/model.json`:

```json
{
  "value": 6.9931640625,
  "previous_value": 6.986328125
}
```

## 9. Observe The Safety Limit

Set the tolerance to `0.0` and change `max_iterations` to `3`. The workflow
cannot converge exactly in three iterations, so it writes the last available
model after reaching the cap:

```json
{
  "value": 6.125,
  "previous_value": 5.25
}
```

This demonstrates that convergence controls normal completion while
`max_iterations` prevents an unbounded computation.

## State Flow

```text
first iteration
  load_initial_model -> Model(0) + cached LocalData
  local sites        -> SiteUpdate values
  server             -> Model(3.5) + cached RemoteState

later iteration
  previous Model + cached LocalData
  local sites        -> new SiteUpdate values
  server + cached RemoteState -> next Model

completion
  final Model -> build_outputs at every site
```

For the complete API contract, see
[Core Components and Workflow](../../core_components_and_workflow.md).
