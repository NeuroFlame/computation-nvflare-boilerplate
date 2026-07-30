# Neuroflame Computation Interface Document

These details explain how Neuroflame manages container initialization,
provisioning, and file mounting. Computation authors do not normally need to
interact with these components, but the details can help when debugging runtime
behavior.

## What Authors Should Know

At the author level, the important contract is:

- local input data appears under `/workspace/data`
- outputs should be written under `/workspace/output`
- run configuration appears under `/workspace/runKit`, including
  `parameters.json` on every runtime node

The framework and runtime layers in the boilerplate already handle those paths.
Computation math code should usually not work with the container setup
directly.

## The System Folder

- **Purpose:**  
  The `/system` folder encapsulates container management and file mounting
  conventions.

- **Contents:**  
  It contains three entry point scripts that run when a container is launched:
  - `entry_central.py` – Launches the central federated client.
  - `entry_edge.py` – Launches the edge federated client.
  - `entry_provision.py` – Executes the provisioning step before a federated run starts.

Central and edge runtime entrypoints remain alive until NVFlare shuts down. A
terminal computation failure is preserved through shutdown and then raised at
the process boundary, producing a nonzero container exit and an error traceback
for the calling platform.

## Provisioning Process

Provisioning generates secure startup packages that allow sites to join a federated network.

### Overview

- **StartupKits and RunKits:**  
  - **StartupKits:** Created by NVFLARE commands during the provisioning step.
  - **RunKits:** NeuroFlame wraps these startupKits into runKits. The
    provisioning code adds the job, server and admin material to the central
    runKit and writes `parameters.json` there.
  
- **Process Flow:**  
  1. **Container Launch:**  
     Neuroflame starts a container using `entry_provision.py`.
  2. **File Operations & Command Execution:**  
     Within the container, file operations and NVFLARE commands generate the startupKits.
  3. **Composition:**  
     The startupKits are wrapped into runKits.
  4. **Distribution:**  
     Once the container exits, Neuroflame zips and distributes the runKits to each site and the central node.
  5. **Client Startup:**  
     Edge and central federated clients receive an event to start their nodes using `entry_edge.py` and `entry_central.py` respectively.

### Provisioning Input

The provisioning container consumes a JSON file named `provision_input.json` with the following structure:

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

- **users:** A non-empty list of active sites. Each `id` and `name` must be a
  non-empty string, and both must be unique. `id` is the stable provisioning
  identity; `name` is the display name exposed through the generated
  `site_id_name_map` parameter.
- **computation_parameters:** A JSON object defined by the consortium leader.
  A string containing an encoded JSON object is also accepted for
  compatibility.
- **fed_learn_port:** The single port used by NeuroFLAME for client and
  administration connections. NeuroFLAME does not currently accept
  `admin_port`; NVFlare 2.8 still supports it as an optional distinct port and
  defaults it to `fed_learn_port` when omitted.
- **host_identifier:** The IP address or hostname for the central node.

## Mounting Conventions

Neuroflame maps host directories into the containers according to the following conventions:

| **Component**              | **Host Directory**                   | **Container Mount Point**  | **Purpose**                                          |
|----------------------------|--------------------------------------|----------------------------|------------------------------------------------------|
| **Provisioning Container** | Run-specific directory (e.g., `run`) | `/provisioning/`           | Temporary workspace for provisioning operations; includes `provision_input.json` written before launch. |
| **Edge Client**            | Run-specific directory/runKit        | `/workspace/runKit`        | Contains startup configuration and must expose `parameters.json` to the framework. |
|                            | Data directory                       | `/workspace/data`          | Read-only site-specific input data.                |
|                            | Output directory                     | `/workspace/output`        | For computation outputs (results, logs, errors).     |
| **Central Client**         | Run-specific directory/runKit        | `/workspace/runKit`        | Contains configuration files including `parameters.json`. |

> **Directory Summary:**  
> - **`/workspace/data`:** Read-only site-specific input data for the computation.  
> - **`/workspace/output`:** Computation outputs, including results, logs, and error reports.  
> - **`/workspace/runKit`:** Configuration files for the computation run. The framework expects `parameters.json` here on both edge and central nodes.
> - **`/provisioning/`:** Used exclusively during the provisioning process.

### Parameter Distribution

The repository's provisioning code writes the canonical `parameters.json` to
the generated `centralNode` runKit. The NeuroFLAME application copies that file
into each edge runKit during distribution, so the runtime executor can load the
same path at every site.

---

- **System Folder:** Manages container entry point scripts.
- **Provisioning:** Wraps NVFLARE startupKits into NeuroFlame runKits and distributes them across the network.
- **Mounting Conventions:** Refer to the table above for a clear mapping of host directories to container paths.

---

This document provides a concise overview of the Neuroflame computation
interface. While computation authors usually should not interact with these
components directly, understanding them helps explain how local data, outputs,
and parameters reach the computation at runtime.
