# Computation Module Publishing Requirements

Use these requirements with the author-facing
[Publishing Computation Images](./publishing_computation_images.md) procedure.
If the repository does not match the intended boilerplate release, complete
[Migrating a Computation](../computation_development/migrating_computations.md)
before release validation.

## Technical Requirements for Dev Team Approval

To gain approval from the development team, the computation module must meet the following technical requirements:

- **Successful Execution**
  - The module must run successfully with three or more sites on the public platform using the provided test data.
  - The declared workflow and generated task configuration must be exercised through `run_local_simulation.sh` before release.

- **Author/Framework Boundary**
  - Computation-specific logic must live under `app/code/computation/`.
  - `app/code/framework/` and `app/code/runtime/` must match the released boilerplate versions used by the computation, excluding ignored bytecode caches.
  - Computation authors must not maintain controller, executor, aggregator, transport, or task-name implementations in the computation layer.

- **Computation Description Document**
  - A clear and comprehensive document must be provided, including:
    - **Algorithm Description** – Explanation of the methodology used.
    - **Limitations** – Any constraints or known issues with the algorithm.
    - **Input Data Specification**:
      - Structure of the **data directory**.
      - Specification for **`parameters.json`**.
    - **Output Format Description** – Clear definition of expected outputs.
    - **Minimum Hardware & Space Requirements** – System requirements for execution.
    - **Basic Dataset Validator** – A tool or script to validate input data format.

- **GitHub Repository**
  - The module must be hosted in a **publicly accessible repository**.
  - The repository should include:
    - A **buildable, working image**.
    - **Test data** for validation. (3 or more sites)
    - The **computation description document**.
    - No generated `job/`, simulator workspace, runtime output, or Python bytecode files staged as source.

- **Versioned container publication**
  - Follow the supported commands and release checklist in
    [Publishing Computation Images](./publishing_computation_images.md).
  - Set the computation release in `.neuroflame-computation-version`.
  - Keep `.neuroflame-computation-api-version` and
    `.neuroflame-boilerplate-version` synchronized through the boilerplate
    migration utility.
  - Configure the registry destination in `.neuroflame-image.json` and publish
    with `./dockerPush.sh`. Do not replace the required OCI labels with labels
    maintained manually in `Dockerfile-prod`.
  - Publishing produces the configured floating tag, a semantic-version tag,
    and a full Git-revision tag. NeuroFLAME resolves one immutable digest from
    these tags before a run.

---

## PI Approval Requirements

Principal Investigators (PIs) are responsible for defining and enforcing additional requirements specific to their computation module. In addition to the general technical requirements, PIs must:

- Document their specific requirements within the computation module’s repository.
- Ensure the module meets the following suggested criteria:

  - **Accuracy & Meaningfulness of Results**
    - Verify that the module produces **valid and meaningful** computational results.
  
  - **Compatibility with Intended Datasets**
    - Confirm that the **data format specification** aligns with intended use cases.
    - Test against **multiple dataset variations** conforming to the specified format.
    - Utilize **real-world datasets** as examples.

  - **Dataset Validator Approval**
    - Approve the basic dataset validator to ensure correct input data formatting.

  - **Additional PI-Specific Requirements**
    - Define any **module-specific** criteria beyond the generic requirements.

---

## **Tracking and Documenting Validation Checks**  

Each computation module repository must maintain version-controlled checklists to track approval status and validation progress. The following checklist files are located in the same directory as this document and should be maintained within the repository:  

- **[DEV_CHECKLIST_TEMPLATE.md](./DEV_CHECKLIST_TEMPLATE.md)**  
  - Tracks **technical requirements** for development team approval.  
  - Documents progress on successful execution, repository setup, and required documentation.  
  - Should be regularly updated with completion status and any pending issues.  

- **[PI_CHECKLIST_TEMPLATE.md](./PI_CHECKLIST_TEMPLATE.md)**  
  - Tracks **PI-specific approval requirements** for accuracy, dataset compatibility, and validation.  
  - Allows PIs to document any additional criteria for module acceptance.  

These checklists must be updated as progress is made and committed to version control to maintain a clear history of approvals, pending actions, and validation status.  
