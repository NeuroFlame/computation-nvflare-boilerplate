from .types import LocalRegressionStatistics, RegressionInputs


def compute_local_statistics(
    inputs: RegressionInputs,
) -> LocalRegressionStatistics:
    return LocalRegressionStatistics(
        xtx=inputs.design_matrix.T @ inputs.design_matrix,
        xty=inputs.design_matrix.T @ inputs.response,
        n_rows=len(inputs.response),
    )
