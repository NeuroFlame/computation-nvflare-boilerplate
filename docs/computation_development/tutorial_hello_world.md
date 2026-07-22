# Hello World Tutorial

This tutorial walks through the current boilerplate example using the new
author-facing model.

The goal is simple:

- each site reads a local list of numbers
- each site computes a local average and count
- the server aggregates those into a global average
- each site writes the final result

You should only need to work inside `app/code/computation/`.

## What You Edit

The boilerplate is organized into three layers:

- `app/code/framework/`
  Shared framework code. Do not edit this for normal computation authoring.
- `app/code/runtime/`
  Thin NVFlare entrypoints. Do not edit this for normal computation authoring.
- `app/code/computation/`
  Author-owned computation code.

For this example, the computation files are:

- `spec.py`
- `types.py`
- `inputs.py`
- `local_math.py`
- `remote_math.py`
- `results.py`

## How The Example Flows

The workflow is declared in
[`app/code/computation/spec.py`](../../app/code/computation/spec.py):

1. `local_step(fn=compute_local_average, input_fn=load_inputs)`
   - each site computes a local summary
2. `remote_step(fn=compute_global_average)`
   - the server aggregates a global average
3. `site_output_step(fn=build_final_outputs)`
   - each site receives the global result
   - each site writes its output files

The framework supplies transport, serialization, paths, logging, and the output
writer; the spec only declares the computation steps.

The local and output function names become generated task identifiers. The
remote function runs on the server as part of the local exchange, so authors do
not declare a separate task name for it.

## Step 1: Define The Data Types

[`app/code/computation/types.py`](../../app/code/computation/types.py)
defines the typed objects used by the computation:

- `ExampleInputs`
- `LocalAverageSummary`
- `GlobalAverageSummary`

These are computation-specific. The framework does not define them for you.
Dataclasses are useful when a payload has named fields, but simple JSON values
can be returned directly without defining a class.

## Step 2: Load Local Inputs

[`app/code/computation/inputs.py`](../../app/code/computation/inputs.py)
loads site-local data from:

- `test_data/site1/data.json`
- `test_data/site2/data.json`
- `test_data/site3/data.json`

The loader returns an `ExampleInputs` object.

For this example, each data file is just a JSON list of numbers.
The framework supplies `data_dir` because the loader requests that exact
parameter name.

## Step 3: Write The Local Math

[`app/code/computation/local_math.py`](../../app/code/computation/local_math.py)
contains the site-side math:

- read the values
- compute the local average
- compute the local count

It returns a `LocalAverageSummary`.

The function's first argument is its input payload. Its optional
`decimal_places` argument is read from `parameters.json` when that key is
present; otherwise the function's Python default is used.

This is the part most authors should spend their time on.

## Step 4: Write The Remote Math

[`app/code/computation/remote_math.py`](../../app/code/computation/remote_math.py)
contains the server-side aggregation:

- collect each site's local average and count
- compute a weighted global average

It returns a `GlobalAverageSummary`.

The function receives `Dict[str, LocalAverageSummary]`. Each key is a site
display name, and the value annotation tells the framework to reconstruct that
site's dataclass. Site arrival order does not affect the aggregation.

## Step 5: Shape The Outputs

[`app/code/computation/results.py`](../../app/code/computation/results.py)
decides what gets written to disk.

For this example, the output is just JSON.

The framework writer handles the actual file writing. Your computation code only
returns the filename and value:

```python
def build_final_outputs(global_summary: GlobalAverageSummary):
    return {"results.json": global_summary}
```

## Run The Example

From the repo root:

```bash
./run_local_simulation.sh site1,site2
```

This will:

- build the local dev image if needed
- create the NVFlare job
- run the simulator
- print the generated output files

The results will be under:

```bash
test_output/simulate_job/site1
test_output/simulate_job/site2
```

## What To Learn From This Example

The important pattern is:

1. load inputs
2. run local math
3. aggregate remotely
4. return outputs

You do not need to manually work with:

- NVFlare controllers
- executors
- aggregators
- `Shareable`
- transport logic
- state persistence
- logger configuration and lifecycle

Those concerns belong in the framework layer.

Receiving annotations are the only typing required by the framework when it
must reconstruct a dataclass. Return annotations remain useful for readers and
type checkers, but they do not control transport.

## Next Step

After this tutorial, move on to the basic regression tutorial:

- [Basic Regression Tutorial](./tutorial_basic_regression.md)

For a repeated local/remote pair, use:

- [Iterative Workflow Tutorial](./tutorial_iterative_workflow.md)
