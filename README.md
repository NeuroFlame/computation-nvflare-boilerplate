## Purpose

The runtime targets NVFlare 2.8.0 and Python 3.11.

## Boilerplate releases

The repository's `.neuroflame.json` manifest records the computation release,
the exact NeuroFLAME computation API and boilerplate compatibility versions,
and the image publishing destination. The boilerplate follows its own semantic
version independently of the NVFlare runtime version. Boilerplate `0.1.0`
targets NVFlare 2.8.0.

Publishing with `./dockerPush.sh` validates this manifest, applies the required
OCI metadata, and pushes the floating, release, and Git-revision tags. Use
`./dockerPush.sh --no-push` to build and inspect the production image without
publishing it.

For a local NeuroFLAME integration test, run `./dockerPush.sh --local`. This
builds all three labeled tags in the local Docker image store and prints the
floating image reference and content-addressed image ID used by the dev client.

Check out the desired boilerplate release, then run its migration utility to
inspect or update a computation repository:

```bash
# Report managed files that differ; makes no changes.
python scripts/migrate_computation.py /path/to/computation --check

# Make a new upgraded working-tree copy without generated files or Git metadata.
python scripts/migrate_computation.py /path/to/computation \
  --output /path/to/upgraded-computation

# Explicitly overwrite framework-owned files in the existing repository.
python scripts/migrate_computation.py /path/to/computation --in-place --force
```

The utility replaces `framework/`, `runtime/`, NVFlare configuration,
provisioning and container integration. It preserves `app/code/computation/`,
repository-specific files, and target-only packages in `requirements.txt`.

Author and release-maintainer procedures are documented in:

- [Migrating a Computation to a Boilerplate Release](docs/computation_development/migrating_computations.md)
- [Publishing Computation Images](docs/computation_publishing/publishing_computation_images.md)

These scripts are repository maintenance tools. NeuroFLAME does not invoke
them while starting or running a computation.

This repository serves as the **central resource** for:

- **Technical documentation** on the NeuroFLAME Computation Interface.
- **Publishing requirements** for computations.
- **Guides, references, and best practices** for developing, validating, and publishing computations on NeuroFLAME.
- A **boilerplate application** to demonstrate basic functionality and provide a starting point for computation development.

## Boilerplate Application

Included in this repository:

- A demonstration of basic NeuroFLAME computation functionality.
- A workflow for developing and testing computations.
- A foundation for new computation projects.

The author-facing framework API is intentionally small:

- `ComputationSpec`
- `stepped_workflow(...)`
- `iterative_workflow(...)`
- `local_step(...)`
- `remote_step(...)`
- `site_output_step(...)`
- `with_state(payload, state)` when a later step needs cached state

Framework-managed artifact transfer remains future-facing and is not part of
the supported author API yet.

Step functions are ordinary Python functions. Their first argument is the step
payload; optional state, framework values, and computation settings are supplied
by exact parameter name.

Requesting `logger` supplies a ready-to-use standard Python logger; computation
authors do not configure its path, handlers, or lifecycle.

Each `local_step` is followed immediately by its `remote_step`, and an optional
`site_output_step` comes last. The framework validates this sequence and derives
the generated job's task identifiers from the declared functions.

For convergence-based computations, `iterative_workflow(...)` repeats one
local/remote pair until `stop_when` returns true or `max_iterations` is reached,
then runs the final `site_output_step` once.

Function names become task identifiers only for local and output steps. Remote
functions and convergence predicates run on the server and can use any
descriptive Python name. The detailed callable, typing, state, and iteration
contracts are in the
[Core Components and Workflow guide](docs/computation_development/core_components_and_workflow.md).

Plain JSON values, nested dataclasses, pandas DataFrames, and bounded NumPy
arrays are serialized by the framework. Computation types do not need payload
methods, codec imports, or dataclass field metadata.

Output functions return a mapping from relative filenames to values, such as
`{"results.json": result, "statistics.csv": dataframe}`. For specialized file
formats, request `output_dir`, write the file directly, and return `None`.

### Quick Start

To get started with the boilerplate application, use:

- [Computation Tutorials](docs/computation_development/tutorials/)
- [Hello World Tutorial](docs/computation_development/tutorials/hello_world/)
- [Basic Regression Tutorial](docs/computation_development/tutorials/basic_regression/)
- [Iterative Workflow Tutorial](docs/computation_development/tutorials/iterative_workflow/)
- [Python Code Standards](docs/computation_development/python_code_standards.md)

For the included example computation, you can also run a local NVFlare simulation directly:

```bash
./run_local_simulation.sh site1,site2
```

This script will:
- build the local dev image
- create the NVFlare job
- run the simulator
- print the generated output files under `test_output/simulate_job/<site>/`

For source-only changes, `--no-build` skips the image build while still testing
the latest repository code through the container bind mount. Rebuild after
changing dependencies or a Dockerfile.

## Author Editing Surface

Computation authors should work inside `app/code/computation/`.

- `spec.py`: choose the workflow and wire the named computation functions together
- `types.py`: define computation-specific data types
- `inputs.py`: load and interpret site-local input data
- `local_math.py`: site-side math
- `remote_math.py`: server-side aggregation math
- `results.py`: shape final outputs

Authors should generally not edit:

- `app/code/framework/`: framework internals
- `app/code/runtime/`: NVFlare adapter layer

The expected author mental model is:

1. load inputs
2. run local math
3. receive aggregated/global input back
4. run more math if needed
5. return final outputs

Framework concerns such as NVFlare controllers, transport, state persistence,
and standard output writing should stay out of computation math code.

## Documentation

- **[Computation Interface Documentation](docs/neuroflame_computation_interface/neuroflame_computation_interface.md)**: How computations interact with NeuroFLAME.
- **[Developer Guides](docs/computation_development/computation_development.md)**: Tips for seamless computation development.
- **[Migration Guide](docs/computation_development/migrating_computations.md)**: Safely apply a released boilerplate to a computation repository.
- **[Image Publishing Guide](docs/computation_publishing/publishing_computation_images.md)**: Build, validate, tag, and publish a computation image.
- **[Publishing Requirements](docs/computation_publishing/Computation_Publishing_Requirements.md)**: Requirements and instructions for publishing.

## Computation Module Library

### Example Computation Modules

- **[mint-computation-single-round-ridge-regression](https://github.com/trendscenter/mint-computation-single-round-ridge-regression)**
- **[flare-file-transfer](https://github.com/dylanmartin/flare-file-transfer/)**

### TReNDS Computation Modules

- **[computation_single_round_ridge_regression_freesurfer](https://github.com/NeuroFlame/computation_single_round_ridge_regression_freesurfer)**
