# Provisioning

## Overview

This document outlines the process NeuroFLAME uses to provision federated networks for their respective studies. It details the inputs required during the provisioning step and specifies the expected outputs.

## Process

The provisioning step creates "runKits," which are folders that each site will use to launch, configure, and connect to the federated network associated with a study run. Once the computation container completes the provisioning step, these runKits will be distributed by NeuroFLAME to the respective sites and the central node. Each runKit will be mounted to the computation containers for both the site and the central node involved in the run.

## Input

The provisioning entry point reads `/provisioning/provision_input.json` by
default. Pass `--input PATH` to use a different file. The file contains the
following fields:

```json
{
    "users": [
        {"id": "unique site ID", "name": "display site name"}
    ],
    "computation_parameters": {"example_parameter": "value"},
    "fed_learn_port": 1234,
    "host_identifier": "IP or hostname"
}
```

- **users**: A non-empty list of active members in the run. Each `id` and
  `name` must be a non-empty string, and both must be unique. `id` is the stable
  provisioning identity; `name` is the display name exposed to computation
  results through the generated `site_id_name_map` parameter.
- **computation_parameters**: A JSON object set by the consortium leader. A
  string containing an encoded JSON object is also accepted for compatibility.
- **host_identifier**: The IP address or hostname where the central node can be reached.
- **fed_learn_port**: The single NVFlare 2.8 port used by clients and the
  administration API to connect to the central node.

The retired `admin_port` field is rejected. NVFlare 2.8 consolidates the
administration and federation listeners on `fed_learn_port` when no separate
admin port is provisioned.

## Output

Provisioning creates one directory per site plus a central-node directory:

```text
/provisioning/runKits/
  <site-id>/
  centralNode/
    admin/
    job/
    server/
    parameters.json
```

Packaging and distribution of those directories are platform responsibilities
after the provisioning container exits.

## Parameter Availability

The framework resolves computation parameters from
`/workspace/runKit/parameters.json` in both central and edge runtime
containers. The provisioning code creates the canonical file in
`centralNode/`; the NeuroFLAME application copies it into each edge runKit when
the runKits are distributed. It is therefore available at the same documented
path on every runtime node.
