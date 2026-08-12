# Core Components and Workflow

This document explains the framework layers authors work around.

The important distinction is:

- authors edit `computation/`
- the framework owns `framework/`
- NVFlare entrypoints live in `runtime/`

## Three Layers

### 1. `computation/`

This is the author-facing layer.

Typical files:

- `spec.py`
- `types.py`
- `inputs.py`
- `local_math.py`
- `remote_math.py`
- `results.py`

This layer should express computation logic.

### 2. `framework/`

This is the shared execution layer.

It owns:

- workflow execution
- local state persistence
- remote state handling
- site ID to display-name mapping
- standard output writing
- runtime context creation

Authors should not normally edit this layer.

### 3. `runtime/`

This is the thin adapter layer that NVFlare loads.

Its job is only to bind the computation spec into generic runtime classes.

Authors should not normally edit this layer.

## Supported Author API

Normal computation code imports only these names from `framework`:

| API | Purpose |
| --- | --- |
| `ComputationSpec(workflow, *, codecs=None, max_inline_array_bytes=8 MiB)` | Binds one workflow to the generic runtime. |
| `stepped_workflow(*steps)` | Runs a declared sequence of local/remote pairs. |
| `iterative_workflow(local, remote, output, *, stop_when=None, max_iterations=50)` | Repeats one local/remote pair before final site output. |
| `local_step(fn, input_fn=None, name=None)` | Declares site-side math and an optional local input loader. |
| `remote_step(fn)` | Declares server-side aggregation for the preceding local step. |
| `site_output_step(fn, name=None)` | Declares final site-side output generation. |
| `with_state(payload, state)` | Returns a normal payload while caching state for later calls. |

`ComputationSpec` only requires `workflow` for the normal case. Its two
keyword-only options are advanced serialization controls. Aggregator IDs,
runtime paths, logger factories, output writers, state type overrides,
transport objects, and internal step types are framework-owned and are not part
of the computation-author interface.

## Stepped Workflows

Authors declare an ordered sequence through `stepped_workflow(...)` with
`local_step(...)`, `remote_step(...)`, and `site_output_step(...)`.

Typical pattern:

1. local sites compute something
2. remote side aggregates it
3. local sites receive the result
4. repeat if needed
5. local sites write outputs

For example:

```python
SPEC = ComputationSpec(
    workflow=stepped_workflow(
        local_step(fn=compute_local_summary, input_fn=load_inputs),
        remote_step(fn=compute_global_result),
        local_step(fn=compute_local_metrics),
        remote_step(fn=combine_metrics),
        site_output_step(fn=build_outputs),
    ),
)
```

Each local/remote pair is one exchange: the local result is collected from all
sites, the remote function receives those site results, and its return value
becomes the payload for the next local or output function. A local step with an
`input_fn` uses the loader's return value instead of the incoming remote payload.
This is normally used only for a step that begins from site-local files.

The workflow is checked as soon as the computation spec is imported:

- a workflow contains at least one step
- every `local_step` is immediately followed by its `remote_step`
- a `remote_step` never appears on its own
- `site_output_step` is optional, but it must be the final step when present
- local and output task names are unique

The framework derives NVFlare task identifiers from local and output function
names and writes them into generated job configuration. Remote functions run on
the server as part of the preceding local task, so their names are not task
identifiers. Authors do not maintain task names in JSON configuration.

The optional `name=` argument is only an escape hatch when the same local or
output function is intentionally reused. Give those declarations distinct
names:

```python
local_step(fn=normalize, input_fn=load_inputs, name="normalize_inputs")
remote_step(fn=aggregate_normalized)
local_step(fn=normalize, name="normalize_results")
remote_step(fn=aggregate_results)
```

## Iterative Workflows

Use `iterative_workflow(...)` when the same local and remote math repeats until
the remote result converges:

```python
def load_initial_model(data_dir):
    inputs = load_site_data(data_dir)
    return with_state(Model.initial(inputs), inputs)


def compute_local_update(model: Model, state: LocalInputs):
    return fit_local_update(model, state)


def compute_global_update(site_updates: Dict[str, ModelUpdate]):
    return merge_updates(site_updates)


def has_converged(model: Model, tolerance=1e-4):
    return model.change < tolerance


def build_outputs(model: Model):
    return {"model.json": model}


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

An iterative workflow deliberately supports one repeated local/remote pair and
one final output step. Use `stepped_workflow(...)` when the computation has
several different phases.

The iterative data flow is fixed:

1. `input_fn` supplies the first payload to the local function.
2. The local result is collected by the remote function.
3. The remote result becomes the next payload to the same local function.
4. `stop_when` checks each remote result.
5. The output function runs once after convergence or the iteration limit.

The initial payload and every remote result should normally have the same type,
because both are passed to the same local function. An iterative `input_fn` runs
only on the first iteration. It can return
`with_state(initial_model, local_data)` to load and persist site data once; the
local function then requests it as `state`.

`stop_when` receives the latest remote result as its first positional argument.
It is an ordinary user-defined synchronous function, and its Python name has no
runtime significance. It does not become an NVFlare task name. It must return a
Python `bool` or NumPy `bool_`:

```python
def done(
    model: Model,
    state: Optional[RemoteState] = None,
    tolerance=1e-4,
):
    state_failed = state is not None and state.failed
    return model.change < tolerance or state_failed
```

The exact name `state` requests remote cached state when one has been created.
Other optional arguments follow the same injection rules as step functions, so
`tolerance` above comes
from computation parameters when present and otherwise uses its Python default.

`stop_when` is optional. Without it, the workflow runs exactly
`max_iterations`. The limit must be a positive integer, defaults to 50, and is
always a safety cap even when a predicate is provided. The output function runs
once with the last remote result whether the workflow converges or reaches the
cap.

## Standard Data Handling

Authors return ordinary Python values. The framework handles:

- JSON values: `None`, booleans, numbers, strings, lists, and dictionaries
- nested dataclasses, including optional and union-typed fields
- pandas `DataFrame` values
- NumPy scalar values and numeric/string arrays

No `to_payload()`, `from_payload()`, codec import, or dataclass field metadata is
needed. For example:

```python
@dataclass
class CachedInputs:
    covariates: pd.DataFrame
    mask: Optional[np.ndarray] = None
```

Type annotations on receiving functions let the framework rebuild
computation-specific dataclasses:

```python
def aggregate(site_results: Dict[str, LocalSummary]):
    ...
```

Annotations are used only where a value crosses a framework boundary and must
be reconstructed. Return annotations are optional and do not control
serialization. Plain JSON values do not need annotations. Without a
computation-specific receiving annotation, a dataclass is received as its plain
dictionary representation. DataFrames and NumPy arrays are self-describing and
remain DataFrames or arrays when nested inside an untyped dictionary.

NumPy arrays are inline transport for small and medium values. The default limit
is 8 MiB per array and can be changed with
`ComputationSpec(max_inline_array_bytes=...)` when the transport cost is known to
be acceptable. Object and structured dtypes are rejected. Oversized arrays,
paths, file handles, raw bytes, and `ArtifactRef` values fail with an actionable
error instead of being silently mis-serialized.

For a genuinely non-standard inline value, register a codec as an advanced
escape hatch. A codec defines `encode(value)` and `decode(payload)`; normal
dataclasses, DataFrames, and arrays do not need one:

```python
from decimal import Decimal


class DecimalCodec:
    @staticmethod
    def encode(value):
        return str(value)

    @staticmethod
    def decode(payload):
        return Decimal(payload)


SPEC = ComputationSpec(
    stepped_workflow(...),
    codecs={Decimal: DecimalCodec},
)
```

Framework-managed artifact transfer is not yet part of the supported author
API. Its internal types are future-facing and should not be used by computation
code yet.

## Function Signatures

Step functions use one predictable calling convention. The first ordinary
argument is the payload for that step:

```python
def compute_local(inputs, decimal_places=2):
    ...


def aggregate_remote(site_results):
    ...


def compute_again(global_result, state: CachedState):
    ...
```

Arguments after the payload are supplied by exact name:

- `state`: the value previously returned through `with_state(...)`
- `parameters`: the complete computation parameters dictionary
- `data_dir`: the site-local input directory
- `output_dir`: the computation output directory
- `logger`: a configured standard Python `logging.Logger`
- any other name: the matching computation parameter, or its Python default

An `input_fn` has no incoming payload, so all of its arguments use the same
name-based injection:

```python
def load_inputs(data_dir, parameters, logger):
    ...
```

The framework creates and closes the logger automatically. Site-side messages
are appended to `<site-id>.log`; server-side messages are appended to
`aggregator.remote.log`. The optional `log_level` computation parameter accepts
`debug`, `info`, `warning`, `error`, or `critical` and defaults to `info`.

A step that does not need its incoming payload can request injected values as
keyword-only arguments:

```python
def build_outputs(*, output_dir):
    ...
```

Use these exact names. The framework rejects aliases such as
`computation_parameters`, `params`, `local_state`, and `remote_state`, as well
as `runtime`, asynchronous functions, `*args`, and `**kwargs`, so signature
mistakes fail directly instead of being silently misinterpreted.

The payload parameter's name is arbitrary; its position makes it the payload.
For example, `model`, `result`, and `site_results` work identically as first
parameters. Reserved and configured values depend on their exact, case-sensitive
names.

### Site Result Containers

A remote function normally receives a dictionary keyed by site display name:

```python
def aggregate(site_results: Dict[str, LocalSummary]):
    for site_name, summary in site_results.items():
        ...
```

The keys make storage and aggregation independent of arrival order. The value
annotation tells the framework to reconstruct each site's `LocalSummary`.
Provisioned IDs are replaced by names from `site_id_name_map` when that mapping
is present; otherwise the site ID is used.

If site identity is genuinely irrelevant, annotating the first parameter as
`List[LocalSummary]` requests only the values. This discards the site keys, so a
dictionary is the safer default.

## State

If later math needs cached data, return `with_state(payload, state)`:

```python
def fit_local(inputs: Inputs):
    summary = fit(inputs)
    return with_state(summary, CachedInputs(inputs.X, inputs.y))


def compute_metrics(global_model: Model, state: CachedInputs):
    return evaluate(global_model, state.X, state.y)
```

There is one local state slot per site and one remote state slot on the server.
Returning a new `with_state(...)` replaces that side's cached value; returning a
plain payload leaves existing state unchanged. Local and remote state are never
mixed or transported as the step payload.

Local state is persisted for the full site workflow, including all iterations.
It is removed after the final `site_output_step` succeeds, with run shutdown as
fallback cleanup. If output generation fails, state remains available until
shutdown. Remote state remains in server memory until run shutdown.

Annotate a dataclass `state` parameter so persisted local state can be rebuilt as
that dataclass. An iterative `input_fn` may establish the initial local cache by
returning `with_state(initial_payload, state)`; normal stepped input loaders
should return only their input payload.

## Output Files

A `site_output_step` normally returns a mapping from relative filename to value:

```python
def build_outputs(result: GlobalResult):
    statistics = build_statistics(result)
    statistics.index.name = "ROI"
    return {
        "results.json": result,
        "statistics.csv": statistics,
        "index.html": build_report(result),
    }
```

The filename extension selects the standard writer:

- `.json`: JSON values, dataclasses, and other framework-serializable values
- `.csv` and `.tsv`: pandas DataFrames or values implementing `to_csv()`
- `.html`, `.htm`, `.md`, and `.txt`: strings

Filenames must be relative to `output_dir`; nested relative paths are allowed.
For CSV files, normal DataFrame settings such as `index.name` determine the
written header.

For specialized formats, request `output_dir`, write the files directly, and
return `None`:

```python
def build_outputs(result, output_dir):
    write_specialized_result(result, output_dir)
```

This is the escape hatch for formats whose writer needs computation-specific
arguments. Large-file transfer between sites remains future artifact work.

## Terminal Failures

Computation authors should raise ordinary Python exceptions for terminal
errors. The framework treats all of the following as run failures:

- exceptions from input, local, remote, convergence, or output functions
- serialization and standard output writer failures
- non-OK NVFlare site results
- task errors, aborts, client death, and timeouts

The framework records the traceback in the computation log and in an internal
`.neuroflame_error.json` marker under the runtime output directory. The marker
exists because NVFlare can log a fatal workflow error while still returning a
successful simulator process status.

Local simulation and production entrypoints inspect that marker after NVFlare
finishes. On failure they raise the recorded error, exit nonzero, and retain the
message and traceback in stderr/container logs. Production entrypoints perform
federation shutdown before the exception reaches the process boundary, allowing
the platform to clean up all containers.

## Typical Author Flow

For a stepped computation, the author mental model should be:

1. load inputs
2. run local math
3. aggregate remotely
4. return outputs

The framework then handles:

- task sequencing
- transport
- state persistence
- mapping provisioned site IDs to display names
- file writing

## Local Simulation Flow

The normal local flow is:

```bash
./run_local_simulation.sh site1,site2
```

That script wraps:

- job creation
- simulator launch
- output inspection

So authors can stay focused on the computation layer instead of simulator setup.

Pass `--no-build` to skip rebuilding the Docker image:

```bash
./run_local_simulation.sh site1,site2 --no-build
```

The repository is bind-mounted into the container, so this still runs the latest
Python and configuration files. Rebuild after changing `Dockerfile-dev`,
`requirements.txt`, or any dependency that must be installed in the image.
