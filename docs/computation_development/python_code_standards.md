# Python Code Standards

The repository uses Ruff to apply consistent, PEP 8-compatible Python style to:

- computation author code in `app/code/computation/`
- shared framework and runtime code
- provisioning and simulation scripts
- tests
- executable tutorial examples

Generated NVFlare jobs, workspaces, and outputs are excluded.

## Quick Setup

From the repository root:

```bash
make setup-dev
make check
```

`make setup-dev` creates an isolated `.venv` and installs the pinned Ruff
version. The other commands also perform this setup automatically when needed.
The computation runtime dependencies do not need to be installed just to lint
or format code.

## Commands

Check lint rules without changing files:

```bash
make lint
```

Check only the author-owned computation directory:

```bash
make lint-author
```

Fix imports and other safe lint violations, then format Python files:

```bash
make format
```

Apply fixes only to author-owned computation code:

```bash
make format-author
```

Confirm that formatting is current without changing files:

```bash
make format-check
```

Run linting, formatting validation, and unit tests:

```bash
make check
```

Run a full computation simulation separately:

```bash
./run_local_simulation.sh site1,site2
```

## Enforced Rules

The root `pyproject.toml` is the authoritative configuration. It enforces:

- Python 3.8-compatible syntax
- Ruff formatting with spaces, double quotes, and an 88-character target
- pycodestyle error and warning checks that do not conflict with the formatter
- undefined-name and unused-import checks
- deterministic import ordering
- common correctness checks from flake8-bugbear
- Google-style PEP 257 docstrings for public modules, packages, classes, methods,
  and functions outside the test suite

Ruff's formatter owns whitespace and line wrapping. A long string that cannot
be split safely may exceed the target without failing lint.

Tests are exempt from docstring rules because their descriptive test names
already document the behavior under test.

## Editor Setup

Ruff integrations for common editors automatically discover `pyproject.toml`
from the repository root. Enable linting and formatting on save if desired, but
run `make check` before committing so the same repository commands validate the
final result.

## Suppressions

Fix a reported issue instead of suppressing it whenever practical. If a rule
does not apply, use the narrowest possible suppression on that line:

```python
import optional_runtime  # noqa: F401
```

Do not add file-wide exclusions or expand `pyproject.toml` ignores for
computation-specific convenience.
