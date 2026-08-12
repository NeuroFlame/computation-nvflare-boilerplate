# Technical Requirements Checklist for Dev Team Approval  

To gain approval from the development team, ensure the computation module meets the following technical requirements.  

## **Successful Execution**  
- [ ] The module runs successfully with **three or more sites** on the public platform using the provided test data.
- [ ] `run_local_simulation.sh` succeeds using the workflow declared in `app/code/computation/spec.py`.

## **Author/Framework Boundary**
- [ ] Computation-specific code is contained in `app/code/computation/`.
- [ ] `app/code/framework/` and `app/code/runtime/` match the released boilerplate versions used by this computation, excluding ignored bytecode caches.
- [ ] The boilerplate migration utility reports no unexpected managed-file differences. See [Migrating a Computation](../computation_development/migrating_computations.md).
- [ ] No computation task names are manually maintained in source NVFlare client configuration.
- [ ] No legacy computation-specific `controller/`, `executor/`, `aggregator/`, or catch-all `utils/` tree is live.

## **Computation Description Document**  
Provide a clear and comprehensive document covering the following:  
- [ ] **Algorithm Description** – Explanation of the methodology used.  
- [ ] **Limitations** – Any constraints or known issues with the algorithm.  
- [ ] **Input Data Specification**:  
   - [ ] Structure of the **data directory**.  
   - [ ] Specification for **`parameters.json`**.  
- [ ] **Output Format Description** – Clear definition of expected outputs.  
- [ ] **Minimum Hardware & Space Requirements** – System requirements for execution.
      Create a log of how many subjects are in each site along with peak RAM usage.
      To track RAM usage, go to docker dashboard, to the specific container and under the 'stats' tab you see RAM usage.
      This info. needs to be included in the compoutation description. Example below:  
      Number of Subjects:RAM Needed (GB)  
            1,824        : 26.62544646  
            327         	: 6.895502383  
            188         	: 4.462923564  
- [ ] **Basic Dataset Validator** – A tool or script to validate input data format.  

## **GitHub Repository**  
Ensure the module is properly hosted and documented:  
- [ ] The module is in a **publicly accessible repository**.  
- [ ] The repository includes:  
   - [ ] A **buildable, working image**.  
   - [ ] **Test data** for validation (**3 or more sites**).  
   - [ ] The **computation description document**.  
   - [ ] Generated jobs, simulator workspaces, runtime output, bytecode, and local reference bundles are excluded unless a reference artifact is intentionally versioned and documented.

## **Versioned Image Publication**
- [ ] `.neuroflame.json` contains the intended `computation.version`.
- [ ] The manifest's `compatibility` section matches the released boilerplate.
- [ ] The manifest's `image` section contains the approved registry repository, floating tag, title, and source URL.
- [ ] `./dockerPush.sh --no-push` builds and validates the production image.
- [ ] `./dockerPush.sh --local` passes the local NeuroFLAME integration test when platform behavior changed.
- [ ] The clean committed release is published with `./dockerPush.sh`, following [Publishing Computation Images](./publishing_computation_images.md).
- [ ] The semantic tag and immutable registry digest are recorded in the release notes.
