# Migrating a Computation to a Boilerplate Release

This is an author and computation-repository maintainer workflow. NeuroFLAME
does not run `migrate_computation.py` when it starts a computation. Use the
script only when deliberately updating a computation repository to a released
boilerplate version.

## What Migration Owns

The migration utility updates the framework-owned integration surface:

- `app/code/framework/`
- `app/code/runtime/`
- `app/config/`
- provisioning code under `system/provision/code/`
- production and development Dockerfiles
- central, edge, and provisioning entrypoints
- job generation and simulator integration
- the image publishing utility
- the manifest schema and `compatibility` section
- boilerplate-managed dependency pins and Docker ignore rules

It preserves:

- `app/code/computation/`
- computation-specific documentation and test data
- repository-specific source files
- target-only packages in `requirements.txt`
- `.neuroflame.json` computation release metadata
- `.neuroflame.json` image names and registry coordinates

Migration records the applied computation API and boilerplate versions in the
`compatibility` section of `.neuroflame.json`. Authors must separately review
`computation.version` and configure the manifest's `image` section; those
values cannot safely be inferred from the boilerplate.

## Before Migrating

1. Commit or otherwise preserve the computation repository's current work.
2. Check out the exact boilerplate release that you intend to apply. Do not run
   the utility from an arbitrary development branch.
3. Confirm that the target contains `app/code/computation/`, a
   `requirements.txt` file, and a valid `.neuroflame.json` with the target's
   computation release and image destination. Copy the manifest structure from
   the boilerplate and replace its author-owned values when upgrading an older,
   unversioned computation.
4. Run the preview mode first.

The utility uses only Python's standard library. Post-migration validation uses
the Python and Docker versions required by the selected boilerplate release.

## Preview Changes

From the checked-out boilerplate repository:

```bash
python scripts/migrate_computation.py /path/to/computation --check
```

This makes no changes. It prints every managed path that differs.

Exit status is:

- `0`: the computation matches the checked-out boilerplate release
- `1`: one or more managed paths differ
- another nonzero status: invalid input or a migration error

The `--check` result covers the framework-owned surface. It does not validate
repository-specific image coordinates or decide whether the computation's own
release number should change.

## Create an Upgraded Copy

The safest first migration creates a new working-tree copy:

```bash
python scripts/migrate_computation.py /path/to/computation \
  --output /path/to/upgraded-computation
```

The output path must not already exist and must be outside the target
repository. The copy excludes Git metadata and generated content such as:

- `.git/`
- `.venv/`
- `.ruff_cache/`
- `__pycache__/`
- `job/`
- `simulator_workspace/`
- `test_output/`
- Python bytecode

Use this mode when comparing releases, evaluating a migration, or preparing a
new branch without touching the original working tree.

## Update In Place

After reviewing the preview, a repository maintainer may explicitly overwrite
framework-owned files in the target:

```bash
python scripts/migrate_computation.py /path/to/computation \
  --in-place --force
```

Both flags are required. The utility stages replacements and restores the old
managed directory if a directory replacement fails, but it is not a substitute
for a clean Git working tree or a backup branch.

Do not manually copy selected framework files between releases. The framework,
runtime, configuration, provisioning, and entrypoint code form one versioned
integration and must be updated together.

## Resolve Computation-Specific Compatibility

After migration, keep necessary compatibility changes inside
`app/code/computation/`. Typical examples include:

- adapting computation code to the boilerplate's supported Python version
- updating a computation-only dependency
- improving validation for an existing parameter contract

Do not reintroduce NVFlare controllers, executors, aggregators, task names, or
transport code into the computation directory.

Review the merged `requirements.txt`. Boilerplate pins replace matching
framework packages; packages found only in the computation repository remain.

## Configure the Computation Release

Verify the author-owned sections of `.neuroflame.json`:

- `computation.version`
- `image`

Normally, do not edit the migration-managed `compatibility` section by hand.
The utility merges compatibility values from the checked-out boilerplate while
preserving the computation and image values.

See [Publishing Computation Images](../computation_publishing/publishing_computation_images.md)
for version rules, image configuration, and release commands.

## Required Validation

From the migrated computation repository:

```bash
make check
./run_local_simulation.sh site1,site2
```

Use at least three sites for release approval when the computation provides
three or more test sites. Rebuild after dependency or Dockerfile changes; use
`--no-build` only for source-only repeat runs.

Then confirm the target matches the selected boilerplate:

```bash
python /path/to/boilerplate/scripts/migrate_computation.py \
  /path/to/computation --check
```

Before publishing, review the computation's numerical and output compatibility,
not only whether the framework-owned files match.

## Troubleshooting

### `--in-place requires --force`

The destructive mode requires both flags so framework files are not
overwritten accidentally. Preview or create a copy first.

### The output path already exists

Choose a new path. The utility never merges into or replaces an existing output
directory.

### Target-only dependencies disappeared or changed

Stop and inspect `requirements.txt`. Target-only exact pins should be retained.
Do not publish until computation-specific dependencies and tests pass.

### `--check` still reports changes

Do not patch framework-owned files locally to silence the check. Determine
whether the migration was incomplete or whether a framework change belongs in
a new boilerplate release.
