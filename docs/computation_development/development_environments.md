# Development Environments

You can develop computations either:

- on your local machine
- inside the dev container

For most author work, the important thing is that local simulation is run from
the project root with `run_local_simulation.sh`.

## Code Quality Setup

Create the lightweight development environment and validate the repository:

```bash
make setup-dev
make check
```

Use `make format` to apply safe lint fixes and format Python code. This setup
installs only the code-quality tooling; it does not duplicate the computation
runtime dependencies installed in the dev container. See
[Python Code Standards](./python_code_standards.md) for the full command and
rule reference.

## Recommended Local Loop

From the repo root:

```bash
./run_local_simulation.sh site1,site2
```

This is the preferred path because it:

- builds the dev image if needed
- creates the local NVFlare job
- runs the simulator
- prints the generated output files

For source-only changes, reuse the existing image:

```bash
./run_local_simulation.sh site1,site2 --no-build
```

`--no-build` skips `docker build`; it does not use stale computation code. The
repository is bind-mounted at `/workspace`, so current Python, configuration,
and documentation files are visible in the container. Run without
`--no-build` after changing `Dockerfile-dev`, `requirements.txt`, or another
image dependency.

## Developing On The Local Machine

Install NVFlare:

```bash
python3 -m pip install nvflare==2.4.0
```

Set the expected environment variables:

```bash
export PYTHONPATH=$PYTHONPATH:[path to this dir + ./app/code/]
export NVFLARE_POC_WORKSPACE=[path to this dir + ./poc-workspace/]
```

This is useful if you want to run scripts, import modules, or debug the Python
code directly from your host environment.

## Developing In The Dev Container

Build the dev image:

```bash
docker build -t nvflare-dev -f Dockerfile-dev .
```

If you need an interactive container shell for lower-level debugging, you can
still use the older container workflow. That is now the exception, not the
normal author path.

## Manual Debug Path

If you need to debug below `run_local_simulation.sh`, the manual steps are:

```bash
python makeJob.py site1,site2
python debugger.py ./job -w ./simulator_workspace -n 2 -c site1,site2
```

Use this only when the wrapper script is not enough for the debugging task.

## Generated Files

Local runs recreate `job/`, `simulator_workspace/`, and
`test_output/simulate_job/`. These are generated validation output and should
remain ignored rather than being committed as computation source.
