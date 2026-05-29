from __future__ import annotations

from src.core.problem import LinearProblem
from src.core.solution import Solution
from src.core.constraint import LinearConstraint
from src.core.bound import VariableBound
from src.analysis.analysis import ExecutionTimes
from src.report.adapters import (
    adapt_single_solution,
    adapt_benchmark,
    adapt_multi_problem,
    ReportData,
    _format_coefficient,
    _format_expression,
    _format_objective,
    _format_constraint_text,
    _format_bound,
    _compute_slack,
    _build_problem_data_text,
)


def test_format_coefficient_positive():
    assert _format_coefficient(3.0, "x") == "3x"


def test_format_coefficient_negative():
    assert _format_coefficient(-2.0, "y") == "-2y"


def test_format_coefficient_one():
    assert _format_coefficient(1.0, "z") == "z"


def test_format_coefficient_neg_one():
    assert _format_coefficient(-1.0, "w") == "-w"


def test_format_expression():
    result = _format_expression({"x": 3.0, "y": 5.0})
    assert result == "3x 5y"


def test_format_expression_negative():
    result = _format_expression({"x": 3.0, "y": -2.0})
    assert "3x" in result
    assert "-2y" in result


def test_format_objective_max():
    result = _format_objective({"x": 3.0, "y": 5.0}, "max")
    assert result == "max Z = 3x 5y"


def test_format_objective_min():
    result = _format_objective({"x": 2.0, "y": 3.0}, "min")
    assert result == "min Z = 2x 3y"


def test_report_data_defaults():
    data = ReportData()
    assert data.variables == {}
    assert data.tables == {}
    assert data.images == {}


def test_report_data_with_values():
    data = ReportData(
        variables={"a": 1},
        tables={"t": (["h"], [["v"]])},
        images={"i": "path.png"},
    )
    assert data.variables["a"] == 1
    assert data.tables["t"] == (["h"], [["v"]])
    assert data.images["i"] == "path.png"


def _make_sample_problem() -> LinearProblem:
    """Create a simple 2-variable LP problem for testing."""
    return LinearProblem(
        objective={"x": 3.0, "y": 5.0},
        sense="max",
        constraints=[
            LinearConstraint(coefficients={"x": 2.0, "y": 1.0}, rhs=18.0, sense="<=", name="c1"),
            LinearConstraint(coefficients={"x": 1.0, "y": 3.0}, rhs=24.0, sense="<=", name="c2"),
        ],
        variables=["x", "y"],
        bounds={
            "x": VariableBound(variable="x", lower=0.0, upper=None),
            "y": VariableBound(variable="y", lower=0.0, upper=None),
        },
        name="test_problem",
        variable_types={"x": "continuous", "y": "continuous"},
    )


def _make_sample_solution() -> Solution:
    return Solution(
        status="OPTIMAL",
        objective_value=42.0,
        variables={"x": 6.0, "y": 6.0},
        dual_values={"c1": 0.5, "c2": 1.5},
        reduced_costs={"x": 0.0, "y": 0.0},
        iterations=3,
    )


def test_adapt_single_solution_basic():
    problem = _make_sample_problem()
    solution = _make_sample_solution()
    times = ExecutionTimes(parse_time=0.01, build_time=0.02, solve_time=0.1, total_time=0.13)
    system_info = {
        "platform": {"system": "Linux", "release": "6.1", "machine": "x86_64",
                     "processor": "Intel", "python_version": "3.14"},
        "hostname": "testbox",
        "timestamp": "2026-01-01T00:00:00",
    }

    data = adapt_single_solution(problem, solution, times, system_info, "highs")

    assert data.variables["solver_name"] == "highs"
    assert data.variables["objective_value"] == "42.0000"
    assert data.variables["num_variables"] == 2
    assert data.variables["num_constraints"] == 2
    assert data.variables["status"] == "OPTIMAL"
    assert data.variables["has_feasible_region"] is False

    assert "constraints_table" in data.tables
    assert "solution_table" in data.tables
    assert "sensitivity_table" in data.tables
    sens_h, sens_r = data.tables["sensitivity_table"]
    assert len(sens_h) == 5


def test_adapt_single_solution_with_charts():
    problem = _make_sample_problem()
    solution = _make_sample_solution()
    times = ExecutionTimes()
    system_info = {"platform": {}, "hostname": "", "timestamp": ""}

    data = adapt_single_solution(
        problem, solution, times, system_info, "highs",
        feasible_region_path="/tmp/chart.png",
        objective_progression_path="/tmp/progress.png",
    )

    assert data.variables["has_feasible_region"] is True
    assert data.variables["feasible_region_path"] == "/tmp/chart.png"
    assert data.variables["objective_progression_path"] == "/tmp/progress.png"
    assert "feasible_region" in data.images
    assert "objective_progression" in data.images


def test_adapt_single_solution_no_charts():
    problem = _make_sample_problem()
    solution = _make_sample_solution()
    times = ExecutionTimes()
    system_info = {"platform": {}, "hostname": "", "timestamp": ""}

    data = adapt_single_solution(
        problem, solution, times, system_info, "highs",
    )

    assert data.variables["has_feasible_region"] is False
    assert data.images == {}


def test_adapt_single_solution_problem_data_text():
    problem = _make_sample_problem()
    solution = _make_sample_solution()
    times = ExecutionTimes()
    system_info = {"platform": {}, "hostname": "", "timestamp": ""}

    data = adapt_single_solution(problem, solution, times, system_info, "highs")
    text = data.variables["problem_data_text"]
    assert "Variables: 2" in text
    assert "Constraints: 2" in text
    assert "x" in text
    assert "y" in text


def test_adapt_single_solution_objective_text():
    problem = _make_sample_problem()
    solution = _make_sample_solution()
    times = ExecutionTimes()
    system_info = {"platform": {}, "hostname": "", "timestamp": ""}

    data = adapt_single_solution(problem, solution, times, system_info, "highs")
    assert data.variables["objective_text"] == "max Z = 3x 5y"


def test_adapt_multi_problem():
    problem = _make_sample_problem()
    solution = _make_sample_solution()

    from src.solver.multi_solver import ProblemResult
    results = [
        ProblemResult(problem=problem, solution=solution, solve_time=0.1),
        ProblemResult(problem=problem, solution=solution, solve_time=0.2),
    ]

    data = adapt_multi_problem(results, "highs")
    assert data.variables["num_problems"] == 2
    assert data.variables["solved"] == 2
    assert data.variables["failed"] == 0

    assert "summary_table" in data.tables
    headers, rows = data.tables["summary_table"]
    assert len(headers) == 5
    assert len(rows) == 2


def test_adapt_multi_problem_with_failures():
    problem = _make_sample_problem()
    sol_ok = _make_sample_solution()
    sol_fail = Solution(status="INFEASIBLE", objective_value=None, variables={})

    from src.solver.multi_solver import ProblemResult
    results = [
        ProblemResult(problem=problem, solution=sol_ok, solve_time=0.1),
        ProblemResult(problem=problem, solution=sol_fail, solve_time=0.0),
    ]

    data = adapt_multi_problem(results, "highs")
    assert data.variables["solved"] == 1
    assert data.variables["failed"] == 1


def test_compute_slack_leq():
    from src.core.constraint import LinearConstraint
    solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 3.0, "y": 2.0})
    c = LinearConstraint(coefficients={"x": 2.0, "y": 1.0}, rhs=10.0, sense="<=")
    slack = _compute_slack(c, solution)
    assert slack == 2.0  # 10 - (2*3 + 1*2) = 2


def test_compute_slack_geq():
    solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 3.0, "y": 2.0})
    c = LinearConstraint(coefficients={"x": 2.0, "y": 1.0}, rhs=5.0, sense=">=")
    slack = _compute_slack(c, solution)
    assert slack == 3.0  # (2*3 + 1*2) - 5 = 3


def test_format_bound_with_lower():
    bound = VariableBound(variable="x", lower=0.0, upper=None)
    assert _format_bound("x", bound) == "x >= 0"


def test_format_bound_with_upper():
    bound = VariableBound(variable="x", lower=None, upper=10.0)
    assert _format_bound("x", bound) == "x <= 10"


def test_format_bound_both():
    bound = VariableBound(variable="x", lower=0.0, upper=10.0)
    assert _format_bound("x", bound) == "0 <= x <= 10"
