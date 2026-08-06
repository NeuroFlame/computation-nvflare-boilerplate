# Basic Computation Development Guide

This guide is the entry point for writing computations with the current
NeuroFLAME boilerplate.

The intended author model is:

1. load inputs
2. run local math
3. aggregate remotely
4. return outputs

Authors should not need to work directly with NVFlare controller, executor,
aggregator, transport, or persistence details.

## Quick Links

- [Computation Tutorials](./tutorials/)
- [Hello World Tutorial](./tutorials/hello_world/)
- [Basic Regression Tutorial](./tutorials/basic_regression/)
- [Iterative Workflow Tutorial](./tutorials/iterative_workflow/)
- [Python Code Standards](./python_code_standards.md)
- [Development Environments](./development_environments.md)
- [Core Components and Workflow](./core_components_and_workflow.md)
- [Migrating a Computation to a Boilerplate Release](./migrating_computations.md)
- [Publishing Computation Images](../computation_publishing/publishing_computation_images.md)
- [Neuroflame Computation Interface Documentation](../neuroflame_computation_interface/neuroflame_computation_interface.md)
- [Algorithm to Computation Module Process](./algorithm_to_computation_module_process.md)

## Directory Structure

Focus on these directories:

- `./app/code/computation/`
  Author-owned computation code.
- `./app/code/framework/`
  Shared framework internals. Do not edit for normal computation authoring.
- `./app/code/runtime/`
  Thin NVFlare entrypoints. Do not edit for normal computation authoring.
- `./app/config/`
  Client/server config used to build the local simulation job.
- `./test_data/<site>/`
  Site-local test data.
- `./test_data/server/parameters.json`
  Parameters used in the local simulation.

## Author Editing Surface

Computation authors should normally work in:

- `spec.py`
- `types.py`
- `inputs.py`
- `local_math.py`
- `remote_math.py`
- `results.py`

The usual responsibilities are:

- `spec.py`
  Declare the workflow.
- `types.py`
  Define computation-specific input/result/state types.
- `inputs.py`
  Load local data.
- `local_math.py`
  Implement site-side computation.
- `remote_math.py`
  Implement server-side aggregation.
- `results.py`
  Shape the output files to be written.

## Framework Model

The supported author API is:

- `ComputationSpec`
- `stepped_workflow(...)`
- `iterative_workflow(...)`
- `local_step(...)`
- `remote_step(...)`
- `site_output_step(...)`
- `with_state(payload, state)` when later steps need cached data

The example boilerplate computation does not need state, so its spec only
declares the workflow. Framework-managed artifact transfer remains
future-facing rather than a supported author feature.

Choose `stepped_workflow(...)` when the computation has a known sequence of
different local/remote phases. Choose `iterative_workflow(...)` when one
local/remote pair repeats until a user-defined predicate returns true or a
safety cap is reached.

Each step function receives its payload as the first argument. Later arguments
are injected by exact name: `state`, `parameters`, `data_dir`, `output_dir`,
`logger`, or a matching key from the computation parameters file. See
[Core Components and Workflow](./core_components_and_workflow.md#function-signatures)
for the complete contract.

`logger` is a ready-to-use standard Python logger created and closed by the
framework.

Computation data can use plain JSON values or nested dataclasses. Type hints on
receiving step functions tell the framework which dataclasses to rebuild.
pandas DataFrames and bounded NumPy arrays are standard field values and need no
codec declarations. See
[Standard Data Handling](./core_components_and_workflow.md#standard-data-handling)
for limits and examples.

Final output functions normally return relative filenames mapped to their
contents. JSON values, DataFrames written as CSV/TSV, and text files are handled
by the standard writer. Specialized formats can be written directly using the
injected `output_dir`. See
[Output Files](./core_components_and_workflow.md#output-files).

## Local Testing

The normal local run path is:

```bash
./run_local_simulation.sh site1,site2
```

This script will:

- build the local dev image if needed
- create the NVFlare job
- run the simulator
- print the generated output files

This should be your default test loop. You do not need to manually run
`dockerRun.sh`, `makeJob.py`, and `debugger.py` unless you are debugging
something lower-level.

Use `--no-build` for Python, documentation, and configuration-only changes. The
repository is mounted into the existing image, so current source is still
tested. Run without `--no-build` after changing image dependencies.

When adopting a new framework release, follow
[Migrating a Computation to a Boilerplate Release](./migrating_computations.md)
instead of copying framework files manually. When the computation is ready for
release, use the author workflow in
[Publishing Computation Images](../computation_publishing/publishing_computation_images.md).

## What Authors Should Avoid

Authors should generally not need to write or reason about:

- controller classes
- executor classes
- aggregator classes
- `Shareable`
- file transport
- state persistence internals
- output path wiring
