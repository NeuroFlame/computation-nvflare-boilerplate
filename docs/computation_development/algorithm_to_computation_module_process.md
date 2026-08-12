### **Guide to Developing Computations for NeuroFLAME**

**Goal**: Create a well-designed computation that integrates seamlessly with the NeuroFLAME platform, works reliably, and produces meaningful results.

---

#### **Step 1: Develop a Working Prototype on Pooled Data**

- **Objective**: Ensure your analysis works correctly on centralized (pooled) data before moving to a federated context.

- **Actions**:
  - **Create a Script**: Write a script (e.g., in Python) that performs your analysis on a single, combined dataset.
  - **Validate Results**: Run the script to confirm it performs the analysis correctly and produces meaningful results.

- **Reasoning**:
  - This step confirms that your analysis logic is sound.
  - There is no point in moving forward if the analysis doesn't work on pooled data.

---

#### **Step 2: Conceptualize the Federated Workflow**

- **Objective**: Understand how your analysis would operate in a federated environment where data remains on local nodes (edge nodes), and only necessary information is shared with a central node.

- **Actions**:
  - **Identify Edge Node Computations**:
    - Determine what parts of the analysis can be performed locally on each dataset without sharing sensitive data.
  - **Define Central Node Computations**:
    - Decide how the central node will aggregate and process the information received from edge nodes.
  - **Collaborate**:
    - Work iteratively, possibly with the development team, to refine the federated approach.

- **Example**:
  - If calculating an average, each edge node computes its local average and count.
  - The central node collects these and computes the global average.

---

#### **Step 3: Prepare Deliverables for NeuroFLAME Integration**

Before integration with NeuroFLAME, provide two key deliverables:

1. **Description of the Federated Workflow**

   - **Purpose**: Clearly explain the sequence of steps that occur across the federated components (edge nodes and central node).

   - **Content**:
     - **Edge Node Steps**:
       - Detail the computations performed locally.
       - Specify what data is sent to the central node.
     - **Central Node Steps**:
       - Describe how it processes the aggregated data.
       - Outline how final results are derived.

   - **Format**:
     - Use diagrams, flowcharts, or bullet points for clarity.

   - **Example**:
     - **Edge Nodes**:
       1. Load local data.
       2. Compute local statistics (e.g., mean, variance).
       3. Send computed statistics to the central node.
     - **Central Node**:
       1. Receive statistics from all edge nodes.
       2. Aggregate the statistics.
       3. Output the final analysis result.

2. **Set of Computation Functions and Boundary Types**

   - **Purpose**: Provide clean functions for local math, remote math, and final output generation.

   - **Content**:
     - **Local Functions**:
       - Functions that process site-local data and produce outputs to be shared.
     - **Remote Functions**:
       - Functions that aggregate site results and compute the next global result.

   - **Specifications**:
     - **Types Where They Help**:
       - Use ordinary dataclasses for structured computation values.
       - Annotate receiving payloads when the framework must reconstruct a dataclass.
       - Plain JSON values need no custom class, and return annotations do not control serialization.
     - **Serializable Data**:
       - Use JSON values, dataclasses, DataFrames, or bounded NumPy arrays for inline payloads.

   - **Example**:

     - **Local Function**:
       ```python
       def compute_local_stats(data: pd.DataFrame) -> LocalStats:
           """
           Computes local statistics.

           Parameters:
               data (pd.DataFrame): The local dataset.

           Returns:
               LocalStats: A typed object containing computed statistics.
           """
           local_mean = data['value'].mean()
           local_count = len(data)
           return LocalStats(local_mean=local_mean, local_count=local_count)
       ```

     - **Remote Function**:
       ```python
       def aggregate_global_stats(local_stats: Dict[str, LocalStats]) -> float:
           """
           Aggregates statistics from sites to compute the global result.

           Parameters:
               local_stats: Statistics keyed by site display name.

           Returns:
               float: The global computed statistic.
           """
           total_sum = sum(
               stat.local_mean * stat.local_count
               for stat in local_stats.values()
           )
           total_count = sum(stat.local_count for stat in local_stats.values())
           global_mean = total_sum / total_count
           return global_mean
       ```

   - **Recommended Mapping To The Boilerplate**:
     - `inputs.py`: local data loading
     - `local_math.py`: local computation
     - `remote_math.py`: remote aggregation
     - `results.py`: final output shaping
     - `spec.py`: workflow declaration

   - **Workflow Declaration**:

     ```python
     SPEC = ComputationSpec(
         workflow=stepped_workflow(
             local_step(fn=compute_local_stats, input_fn=load_inputs),
             remote_step(fn=aggregate_global_stats),
             site_output_step(fn=build_outputs),
         ),
     )
     ```

     Use `iterative_workflow(...)` instead when the same local and remote
     functions repeat until convergence. Computation authors do not write task
     names, controllers, executors, aggregators, or payload conversion methods.

---

### **Final Notes**

- **Review and Testing**:
  - Test your functions with sample data to ensure they work as expected.
  - Verify that data types and structures are consistent and correctly defined.

- **Documentation**:
  - Provide comments and docstrings in your code for clarity.
  - Include any assumptions or prerequisites in your workflow description.

- **Collaboration**:
  - Share your deliverables with the NeuroFLAME development team.
  - Be open to feedback and ready to refine your computations as needed.

---

### **Summary**

By following these steps and preparing the specified deliverables, you set a solid foundation for integrating your computation with NeuroFLAME:

1. **Working Prototype**: Validate your analysis on pooled data to ensure correctness.
2. **Conceptual Federated Workflow**: Plan how your analysis will function in a federated environment.
3. **Deliverables**:
   - **Workflow Description**: A clear outline of the federated computation steps.
   - **Computation Functions**: Clean local, remote, and output math with boundary types where reconstruction requires them.

This structured approach helps focus your efforts, validates the fundamental elements of your computation, and facilitates collaboration with the development team. It ensures that the final integrated computation is reliable and produces meaningful results.

---

**Remember**: The key is to start with a solid foundation (working pooled data analysis) and then thoughtfully adapt it for the federated context, clearly documenting each step along the way.
