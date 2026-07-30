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

See the official [NVFlare 2.8 migration guide](https://nvflare.readthedocs.io/en/2.8.0/migration_guide.html),
[provisioning guide](https://nvflare.readthedocs.io/en/2.8.0/programming_guide/provisioning_system.html),
and [simulator guide](https://nvflare.readthedocs.io/en/2.8.0/user_guide/nvflare_cli/fl_simulator.html).
