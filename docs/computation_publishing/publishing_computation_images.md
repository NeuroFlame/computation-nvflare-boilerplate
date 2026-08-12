# Publishing Computation Images

This is the supported author and release-maintainer workflow for building and
publishing a NeuroFLAME computation image. NeuroFLAME does not invoke
`dockerPush.sh` during a run. At runtime, the platform inspects the published
image metadata and resolves the configured image to an immutable digest.

For a release, use `dockerPush.sh` rather than a manual `docker build`,
`docker tag`, or `docker push` sequence. The script owns the required labels and
tag layout.

## Prerequisites

- Docker is installed and running.
- The repository has been migrated to the intended boilerplate release.
- `make check` and the required local simulations pass.
- The Git revision being published contains all tracked source changes.
- You are authenticated to the configured registry and have push permission.
- The release version and image configuration have been reviewed.

Publishing refuses to push when tracked files differ from `HEAD`. Commit the
release source before publishing. Local-only and validation-only builds may use
a dirty working tree for development, but their revision label still describes
the selected Git commit, so do not treat them as releases.

## Required Repository Metadata

`.neuroflame.json` is the single versioned manifest for computation release,
compatibility, and image publishing metadata:

```json
{
  "manifestVersion": 1,
  "computation": {
    "version": "0.1.0"
  },
  "compatibility": {
    "computationApiVersion": "0.1.0",
    "boilerplateVersion": "0.1.0"
  },
  "image": {
    "title": "my-neuroflame-computation",
    "repository": "my-registry-user/my-neuroflame-computation",
    "floatingTag": "latest",
    "tagPrefix": "",
    "source": "https://github.com/example/my-neuroflame-computation"
  }
}
```

`manifestVersion` identifies the manifest schema and is not the computation or
API release.

Authors own:

- `computation.version`: the computation application's semantic version
- `image`: repository-specific OCI and registry configuration

The boilerplate migration owns:

- `compatibility.computationApiVersion`: the NeuroFLAME computation API
  contract expected by the image
- `compatibility.boilerplateVersion`: the framework/runtime release applied to
  the repository

Increment `computation.version` whenever releasing changed computation code or
behavior. A patch release is appropriate for backward-compatible fixes. Minor
or major changes should reflect the computation project's compatibility
policy. Do not change the compatibility versions merely to release new math;
apply the corresponding boilerplate release instead.

NeuroFLAME accepts patch-level differences within the same API major/minor
line. A major or minor API mismatch requires the application or computation
image to be updated.

### NVFlare runtime

`requirements.txt` must contain exactly one strict pin:

```text
nvflare==2.8.0
```

The publisher reads this pin for the runtime compatibility label.

Image fields are:

- `title`: OCI image title inspected by NeuroFLAME
- `repository`: registry repository without a tag
- `floatingTag`: moving tag used when selecting the computation
- `tagPrefix`: optional prefix added to release and revision tags
- `source`: canonical source repository URL

Do not put required OCI or NeuroFLAME labels directly in `Dockerfile-prod`.
The publishing script derives and validates them from `.neuroflame.json`, the
NVFlare dependency pin, and the Git revision.

## Local NeuroFLAME Development Build

Build all release-shaped tags in the local Docker image store without pushing:

```bash
./dockerPush.sh --local
```

This is the normal command for testing a computation image with a local
NeuroFLAME development environment. It prints:

- the floating image reference
- the content-addressed local image ID

The platform's local-image mode uses that local image rather than requiring a
registry or a testing-only database field.

## Build and Validate Without Pushing

To exercise the production Dockerfile, labels, and tags without publishing:

```bash
./dockerPush.sh --no-push
```

Use this in release preparation and CI validation. It builds and inspects the
image but performs no registry push.

## Publish a Release

The default command publishes:

```bash
./dockerPush.sh
```

This command pushes three tags:

```text
<repository>:<floatingTag>
<repository>:<tagPrefix><computation-version>
<repository>:<tagPrefix><full-git-revision>
```

It then prints the immutable registry digest. Record that digest in release or
deployment notes when traceability is required.

The default platform is `linux/amd64`, which is the supported NeuroFLAME
computation target. Do not override `--platform` for a normal release. A
different platform requires an explicit platform compatibility decision.

An explicit revision can be supplied as the positional argument, but normal
author releases should omit it and publish the current `HEAD`:

```bash
./dockerPush.sh <git-revision>
```

Review all options with:

```bash
./dockerPush.sh --help
```

## Generated Labels

The script adds and validates:

- `org.opencontainers.image.title`
- `org.opencontainers.image.version`
- `org.opencontainers.image.revision`
- `org.opencontainers.image.source`
- `org.neuroflame.computation-api.version`
- `org.neuroflame.boilerplate.version`
- `org.neuroflame.nvflare.version`

These labels are the preflight contract inspected by NeuroFLAME before a run.
Changing a Docker tag alone does not change the compatibility metadata.

## Author Release Checklist

1. Apply the intended boilerplate release with
   [the migration utility](../computation_development/migrating_computations.md).
2. Review computation-specific dependencies and behavior.
3. Update `computation.version` in `.neuroflame.json`.
4. Verify the manifest's `compatibility` and `image` sections.
5. Run `make check`.
6. Run the required multi-site local simulation.
7. Build and validate with `./dockerPush.sh --no-push`.
8. Test locally with `./dockerPush.sh --local` when changing platform
   integration.
9. Commit all tracked release source and verify `git status`.
10. Authenticate to the registry and run `./dockerPush.sh`.
11. Record the published semantic tag and immutable digest.

## Troubleshooting

### Refusing to publish with tracked uncommitted changes

The image revision label must identify the source that was built. Commit the
tracked changes, then publish again. Do not bypass the check with a manual push.

### Missing required image configuration

Create or correct `.neuroflame.json`. Migration updates only its compatibility
section; it cannot infer registry ownership, source URLs, the desired floating
tag, or the computation release.

### Invalid semantic version

Each version field in `.neuroflame.json` must contain only
`MAJOR.MINOR.PATCH`. Do not add a `v` prefix or prerelease suffix.

### Registry authentication or authorization failure

Log in using the registry's supported Docker authentication flow and verify
that the configured `repository` belongs to an account or organization where
you can push.

### NeuroFLAME reports a missing label

Rebuild with `dockerPush.sh`. An older or manually built local image may share
the same floating tag without containing the required labels.
