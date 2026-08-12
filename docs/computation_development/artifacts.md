# Computation Artifacts

Use an artifact when a computation step needs to exchange a file whose bytes
should not be serialized into an NVFlare `Shareable`.

```python
from framework import artifact


def compute_site_summary(inputs, *, artifact_dir):
    output_path = write_summary_file(inputs, artifact_dir)
    return {
        "summary": artifact(
            "site-summary.npy",
            output_path,
            "application/x-neuroflame-numpy-array",
        )
    }
```

The author API is deliberately limited to `artifact(name, path,
media_type=None)`. The workflow edge determines ownership and routing: a local
step result is site-to-central, and a remote step result is central-to-sites.
Authors do not select peers, transport channels, destination roots, chunking,
or retries.

The file must be created below the injected `artifact_dir`. Names are logical
identifiers, not destination paths, and may contain only letters, numbers,
periods, underscores, and hyphens. The runtime rejects traversal, symlinks,
non-regular files, per-file limit violations, and aggregate limit violations.
It snapshots each approved source with no-follow file access and owner-only
permissions before advertising the transfer.

Only a small manifest is placed in the task `Shareable`: an opaque transfer ID,
logical name, media type, byte length, SHA-256 digest, workflow stage, and
direction. Artifact bytes use NVFlare 2.8's public
[`FileStreamer`](https://nvflare.readthedocs.io/en/2.8.0/apidocs/nvflare.app_common.streamers.file_streamer.html)
registration, streaming, and completion-callback APIs. `FileStreamer` is a
blocking file API with bounded chunks (1 MiB by default) and per-chunk timeouts.
The runtime owns its opaque auxiliary-request transaction key and does not
depend on `FileRetriever`'s private transaction table or callbacks.

NVFlare validates chunk and final byte counts, but its file API does not define
an application content hash or final application filename. NeuroFLAME therefore
adds SHA-256 verification, opaque staging names, atomic promotion, duplicate
delivery detection, bounded retry, and end-of-run cleanup around the supported
streamer. Provisioned streams require NVFlare P2P security in addition to the
transport connection. NVFlare 2.8's in-process simulator cannot exchange P2P
certificates, so the runtime disables that additional layer only when NVFlare's
own `FLContextKey.SIMULATE_MODE` is true. A completed file is never exposed to
computation code until its size and digest match the manifest.

Defaults are configured on `ComputationSpec`:

- `max_artifact_bytes`: 512 MiB per file
- `max_artifact_total_bytes`: 1 GiB per payload and cumulative central round
- `artifact_timeout`: 300 seconds per attempt
- `artifact_retries`: two retries after a completed but invalid transfer

NVFlare 2.8 does not expose per-file-stream cancellation. A timeout or run
abort is therefore treated as indeterminate and is not retried concurrently.
The runtime retains a bounded completion tombstone and its quota reservation so
any late temporary file is identified and removed. At terminal transport
shutdown it force-clears tombstones and receiver staging; active blocking
senders finish before their staging is removed. Retries remain available after
a completed stream fails size or hash verification.

The runtime keeps detailed failures only in the participant's local terminal
error record. Transported error envelopes contain only an allowlisted schema
version, stage, origin, and error code; they
do not include artifact contents, hashes, local paths, or subject-level data.
All successful, partial, and failed transfer staging is removed at `END_RUN` or
as soon as an already-active late stream finishes. Provisioned participant kits
also set `allow_log_streaming` to `false`; computation and error logs stay local
unless a participant deliberately changes its site policy outside the generated
kit.

NVFlare's 2.8
[`StreamableEngine`](https://nvflare.readthedocs.io/en/2.8.0/apidocs/nvflare.apis.streaming.html)
supports multiple streaming sessions, and the simulator runs clients in
separate worker processes. Artifact IDs and receiver directories are isolated
per source and transfer, so concurrent participant pulls do not share a
destination filename.
