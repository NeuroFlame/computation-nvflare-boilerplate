# NVFlare 2.8 Runtime

NeuroFlame uses NVFlare 2.8.0 on Python 3.11. Computation authors continue to
work only in `app/code/computation/`; the NVFlare controller, executor,
aggregator, provisioning, and simulator integration remain framework concerns.

Provisioning uses NeuroFLAME's single-port server contract. Supply
`fed_learn_port`; this wrapper rejects `admin_port`, although NVFlare 2.8 still
supports a distinct optional administration port and defaults it to
`fed_learn_port` when omitted. Generated projects contain no HA or Overseer
configuration. The server and client
`local/resources.json.default` files retain NVFlare's provisioned class allow
list and add only the reviewed NeuroFlame runtime entrypoint classes.

Local development uses the public `nvflare simulator` command for traditional
jobs. The wrapper creates the simulator workspace's NVFlare 2.8 component
authorization policy for `nvflare.` and framework-owned `runtime.` classes;
computation author modules are not exposed as NVFlare components. The wrapper
inspects `.neuroflame_error.json` after the command finishes so an unhandled
computation exception still reaches the calling process and produces a nonzero
exit.

NVFlare converts executor exceptions to return codes at the client task
boundary. To retain failure provenance without exporting participant data, the
wrapper returns `EXECUTION_EXCEPTION` with a versioned envelope containing only
`origin`, `stage`, and `scope`. Full exception messages and tracebacks remain in
the failing site's private marker and log. Controllers preserve the envelope's
site origin; central controller and aggregation failures use central origin.

Computation authors adopting this runtime should not copy these integration
files individually. Apply the released framework with
[Migrating a Computation](../computation_development/migrating_computations.md),
then use [Publishing Computation Images](../computation_publishing/publishing_computation_images.md)
to build and publish the labeled image.

See the official [NVFlare 2.8 migration guide](https://nvflare.readthedocs.io/en/2.8.0/migration_guide.html),
[provisioning guide](https://nvflare.readthedocs.io/en/2.8.0/programming_guide/provisioning_system.html),
and [simulator guide](https://nvflare.readthedocs.io/en/2.8.0/user_guide/nvflare_cli/fl_simulator.html).
