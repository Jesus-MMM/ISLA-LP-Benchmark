from src.report.adapters.types import ReportData
from src.report.adapters.formatters import (
    _format_coefficient,
    _format_expression,
    _format_objective,
    _format_constraint_text,
    _format_bound,
    _compute_slack,
    _get_constraint_name,
    _get_constraint_name_from_sensitivity,
    _get_solver_version,
    _build_solver_log_table,
    _build_objective_with_vars,
    _build_problem_data_text,
    _build_performance_matrix,
    _get_problem_from_result,
    _build_recommendations,
)
from src.report.adapters.single import adapt_single_solution
from src.report.adapters.benchmark import adapt_benchmark, _build_solver_note
from src.report.adapters.multi import adapt_multi_problem

__all__ = [
    "ReportData",
    "adapt_single_solution",
    "adapt_benchmark",
    "adapt_multi_problem",
    "_format_coefficient",
    "_format_expression",
    "_format_objective",
    "_format_constraint_text",
    "_format_bound",
    "_compute_slack",
    "_get_constraint_name",
    "_get_constraint_name_from_sensitivity",
    "_get_solver_version",
    "_build_solver_log_table",
    "_build_solver_note",
    "_build_objective_with_vars",
    "_build_problem_data_text",
    "_build_performance_matrix",
    "_get_problem_from_result",
    "_build_recommendations",
]
