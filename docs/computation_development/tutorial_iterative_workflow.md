# Iterative Workflow Tutorial

This tutorial shows the complete author-facing shape for math that repeats the
same local and remote update until a server-side condition is met.

Use an iterative workflow when the algorithm is naturally:

1. initialize a model at each site
2. compute one local update
3. combine site updates remotely
4. repeat with the combined model
5. stop on convergence or a safety limit
6. write the final result at each site

The framework owns the loop, task scheduling, transport, serialization, state
persistence, and logging lifecycle.

## Define Computation Types

In `types.py`:

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

These are ordinary dataclasses. They do not need payload methods, framework
base classes, or field metadata.

## Load The Initial Model Once

In `inputs.py`:

```python
import json
import os

from framework import with_state

from .types import LocalData, Model


def load_initial_model(data_dir):
    with open(os.path.join(data_dir, "data.json"), encoding="utf-8") as data_file:
        observations = json.load(data_file)

    local_data = LocalData(observations=observations)
    return with_state(Model(value=0.0), local_data)
```

For an iterative workflow, `input_fn` runs only on the first iteration.
Returning `with_state(initial_model, local_data)` sends the model into the first
local call and caches the site data for every later call.

## Write The Repeated Local Math

In `local_math.py`:

```python
from .types import LocalData, Model, SiteUpdate


def compute_local_update(model: Model, state: LocalData):
    local_mean = sum(state.observations) / len(state.observations)
    estimate = (model.value + local_mean) / 2
    return SiteUpdate(estimate=estimate)
```

The first argument receives either the initial model or the previous remote
result. The exact name `state` requests the cached `LocalData`.

## Combine Site Updates

In `remote_math.py`:

```python
from typing import Dict, Optional

from framework import with_state

from .types import Model, RemoteState, SiteUpdate


def compute_global_update(
    site_updates: Dict[str, SiteUpdate],
    state: Optional[RemoteState] = None,
):
    value = sum(update.estimate for update in site_updates.values()) / len(site_updates)
    previous_value = None if state is None else state.value
    model = Model(value=value, previous_value=previous_value)
    return with_state(model, RemoteState(value=value))
```

The dictionary keys are site display names, so aggregation does not depend on
arrival order. The framework reconstructs every value as `SiteUpdate` from the
annotation. Remote state stays on the server and is supplied to the next remote
call.

## Define Convergence

The convergence predicate can live beside the remote math:

```python
def has_converged(model: Model, tolerance=1e-4):
    if model.previous_value is None:
        return False
    return abs(model.value - model.previous_value) <= tolerance
```

This is an ordinary user-defined function:

- its first argument receives the latest remote result
- its Python name does not matter
- it does not become a task name
- `tolerance` is injected from computation parameters or uses its default
- it must return a Python `bool` or NumPy `bool_`

## Build Final Outputs

In `results.py`:

```python
from .types import Model


def build_outputs(model: Model):
    return {"model.json": model}
```

The output function runs once after convergence or after the iteration cap.

## Declare The Workflow

In `spec.py`:

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

No task names, rounds, controller code, executor code, aggregator code, or
serialization methods are required.

If `stop_when` is omitted, the pair runs exactly `max_iterations` times. If the
predicate never returns true, `max_iterations` remains the safety cap and the
last remote result is still passed to `build_outputs`.

## Run It

From the repository root:

```bash
./run_local_simulation.sh site1,site2
```

During source-only iteration, reuse the existing image with:

```bash
./run_local_simulation.sh site1,site2 --no-build
```

`--no-build` still runs current repository code because the repository is
mounted into the container. Rebuild when dependencies or the Dockerfile change.
