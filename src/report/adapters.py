from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.core.problem import LinearProblem
from src.core.solution import Solution
from src.solver.multi_solver import ProblemResult
from src.solver.benchmark import BenchmarkRunner
from src.analysis.analysis import ExecutionTimes


@dataclass
class ReportData:
    """Container for data extracted from LP domain objects.

    Attributes:
        variables: Key-value pairs for {{variable}} template substitution.
        tables: Table name to (headers, rows) for programmatic injection.
        images: Image ID to file path for chart/plot references.
    """
    variables: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, tuple[list[str], list[list[str]]]] = field(default_factory=dict)
    images: dict[str, str] = field(default_factory=dict)


def _format_coefficient(coeff: float, var: str) -> str:
    """Format a single term like '3x' or '-2y'."""
    if coeff == 1.0:
        return var
    if coeff == -1.0:
        return f"-{var}"
    if coeff == int(coeff):
        coeff_str = str(int(coeff))
    else:
        coeff_str = str(coeff)
    if coeff >= 0:
        return f"{coeff_str}{var}"
    return f"{coeff_str}{var}"


def _format_expression(coefficients: dict[str, float]) -> str:
    """Build an expression string from a coefficient dict."""
    if not coefficients:
        return "0"
    terms = []
    for var, coeff in coefficients.items():
        term = _format_coefficient(coeff, var)
        terms.append(term)
    expr = " ".join(terms)
    if expr.startswith("-"):
        return expr
    if expr.startswith("+"):
        return expr[1:]
    return expr


def _format_objective(obj: dict[str, float], sense: str) -> str:
    """Format an objective function string.

    Example: 'max Z = 3x + 5y'
    """
    expr = _format_expression(obj)
    return f"{sense} Z = {expr}"


def _format_constraint_text(c: Any) -> str:
    """Format a single constraint as readable text.

    Example: '2x + 3y <= 10'
    """
    expr = _format_expression(c.coefficients)
    return f"{expr} {c.sense} {c.rhs}"


def _format_bound(var: str, bound: Any) -> str:
    """Format a variable bound.

    Example: '0 <= x <= 100' or 'x >= 0' or 'x <= 100'
    """
    lo = bound.lower
    up = bound.upper

    def _fmt(val: float) -> str:
        return str(int(val)) if val == int(val) else str(val)

    if lo is not None and up is not None:
        return f"{_fmt(lo)} <= {var} <= {_fmt(up)}"
    elif lo is not None:
        return f"{var} >= {_fmt(lo)}"
    elif up is not None:
        return f"{var} <= {_fmt(up)}"
    return var


def adapt_single_solution(
    problem: LinearProblem,
    solution: Solution,
    times: ExecutionTimes,
    system_info: dict[str, Any],
    solver_name: str,
    feasible_region_path: Optional[str] = None,
    objective_progression_path: Optional[str] = None,
    author: str = "",
) -> ReportData:
    """Convert a single LP solution into report data.

    Args:
        problem: The LP problem model.
        solution: The solved solution.
        times: Execution timing breakdown.
        system_info: System/platform information dict.
        solver_name: Name of the solver used.
        feasible_region_path: Path to feasible region chart PNG (optional).
        objective_progression_path: Path to objective progression chart PNG (optional).
        author: Report author name.

    Returns:
        ReportData with variables, tables and images ready for the engine.
    """
    data = ReportData()

    # --- Variables ---
    plat = system_info.get("platform", {})
    has_charts = feasible_region_path is not None and objective_progression_path is not None

    data.variables = {
        "solver_name": solver_name,
        "status": solution.status,
        "objective_value": f"{solution.objective_value:.4f}" if solution.objective_value is not None else "N/A",
        "num_variables": len(problem.variables),
        "num_constraints": len(problem.constraints),
        "problem_type": problem.sense.upper(),
        "parse_time_ms": f"{times.parse_time * 1000:.2f}",
        "build_time_ms": f"{times.build_time * 1000:.2f}",
        "solve_time_ms": f"{times.solve_time * 1000:.2f}",
        "total_time_ms": f"{times.total_time * 1000:.2f}",
        "system_os": f"{plat.get('system', '?')} {plat.get('release', '?')}",
        "system_python": plat.get("python_version", "?"),
        "hostname": system_info.get("hostname", "?"),
        "timestamp": system_info.get("timestamp", datetime.now().isoformat()),
        "author": author or "Operations Research Laboratory",
        "author_label": f"Prepared by: {author}" if author else "Operations Research Laboratory",
        "problem_data_text": _build_problem_data_text(problem),
        "objective_text": _format_objective(problem.objective, problem.sense),
        "has_feasible_region": has_charts,
        "feasible_region_path": (feasible_region_path.replace("\\", "/") if feasible_region_path else ""),
        "objective_progression_path": (objective_progression_path.replace("\\", "/") if objective_progression_path else ""),
    }

    # --- Tables: constraints ---
    constraint_headers = ["Constraint", "Expression", "RHS", "Sense", "Slack"]
    constraint_rows = []
    for c in problem.constraints:
        slack = _compute_slack(c, solution)
        slack_str = f"{slack:.4f}" if slack is not None else "N/A"
        name = getattr(c, "name", "") or f"c{len(constraint_rows) + 1}"
        constraint_rows.append([
            name,
            _format_expression(c.coefficients),
            str(c.rhs),
            c.sense,
            slack_str,
        ])
    data.tables["constraints_table"] = (constraint_headers, constraint_rows)

    # --- Tables: optimal solution ---
    sol_headers = ["Variable", "Value", "Type", "Reduced Cost"]
    sol_rows = []
    for var in problem.variables:
        val = solution.variables.get(var, 0.0)
        vtype = problem.variable_types.get(var, "continuous")
        rc = solution.reduced_costs.get(var, 0.0) if solution.reduced_costs else 0.0
        sol_rows.append([var, f"{val:.4f}", vtype, f"{rc:.4f}"])
    data.tables["solution_table"] = (sol_headers, sol_rows)

    # --- Tables: sensitivity ---
    sens = solution.sensitivity
    sens_headers = ["Variable", "Current", "Lower", "Upper", "Reduced Cost"]
    sens_rows = []
    if sens and hasattr(sens, "objective_ranges"):
        for sr in sens.objective_ranges:
            lo = f"{sr.lower:.4f}" if sr.lower is not None else "-inf"
            up = f"{sr.upper:.4f}" if sr.upper is not None else "+inf"
            rc = f"{sr.reduced_cost:.4f}" if sr.reduced_cost is not None else "N/A"
            sens_rows.append([
                sr.name,
                f"{sr.current:.4f}",
                lo,
                up,
                rc,
            ])
    if not sens_rows:
        sens_rows.append(["N/A", "N/A", "N/A", "N/A", "N/A"])
    data.tables["sensitivity_table"] = (sens_headers, sens_rows)

    # --- Images ---
    if has_charts:
        data.images["feasible_region"] = feasible_region_path
        data.images["objective_progression"] = objective_progression_path

    return data


def adapt_benchmark(
    runner: BenchmarkRunner,
    system_info: dict[str, Any],
    chart_dir: Optional[Path] = None,
) -> ReportData:
    """Convert benchmark results into report data.

    Args:
        runner: The benchmark runner with completed results.
        system_info: System/platform information.
        chart_dir: Directory containing pre-generated chart PNGs.

    Returns:
        ReportData for benchmark_report.csv template.
    """
    data = ReportData()
    summary = runner.get_summary()

    by_solver = summary.get("by_solver", {})
    solvers = sorted(by_solver.keys())
    num_solvers = len(solvers)
    num_problems = summary.get("total_benchmarks", 0) // max(num_solvers, 1)

    plat = system_info.get("platform", {})

    # --- Chart paths ---
    chart_dir_val = Path(chart_dir) if chart_dir else Path(".")
    chart_paths = {}
    chart_file_map = {
        "time_chart": "benchmark_times.png",
        "success_chart": "benchmark_success.png",
        "profile_chart": "benchmark_profile.png",
        "scalability_chart": "benchmark_dashboard.png",
    }
    for chart_name, filename in chart_file_map.items():
        p = chart_dir_val / filename
        chart_paths[chart_name] = str(p).replace("\\", "/") if p.exists() else ""

    data.variables = {
        "num_problems": num_problems,
        "num_solvers": num_solvers,
        "total_benchmarks": summary.get("total_benchmarks", 0),
        "successful": summary.get("successful", 0),
        "failed": summary.get("failed", 0),
        "system_os": f"{plat.get('system', '?')} {plat.get('release', '?')}",
        "system_python": plat.get("python_version", "?"),
        "hostname": system_info.get("hostname", "?"),
        "timestamp": system_info.get("timestamp", datetime.now().isoformat()),
        "time_chart_path": chart_paths.get("time_chart", ""),
        "success_chart_path": chart_paths.get("success_chart", ""),
        "profile_chart_path": chart_paths.get("profile_chart", ""),
        "scalability_chart_path": chart_paths.get("scalability_chart", ""),
    }

    # --- Table: statistics summary ---
    stat_headers = ["Metric", "Value"]
    stat_rows = [
        ["Total Benchmarks", str(data.variables["total_benchmarks"])],
        ["Successful", str(data.variables["successful"])],
        ["Failed", str(data.variables["failed"])],
        ["Solvers", str(num_solvers)],
        ["Problems", str(num_problems)],
    ]
    data.tables["stats_table"] = (stat_headers, stat_rows)

    # --- Table: solver comparison ---
    comp_headers = ["Solver", "Runs", "Success", "Avg Time (s)", "Min Time (s)",
                    "Max Time (s)", "Std Dev", "Avg Memory (MB)", "Peak Memory (MB)"]
    comp_rows = []
    for s_name in solvers:
        info = by_solver[s_name]
        comp_rows.append([
            s_name,
            str(info.get("runs", 0)),
            str(info.get("successful", 0)),
            f"{info.get('avg_time', 0):.4f}",
            f"{info.get('min_time', 0):.4f}",
            f"{info.get('max_time', 0):.4f}",
            f"{info.get('std_time', 0):.4f}",
            f"{info.get('avg_memory', 0):.2f}",
            f"{info.get('peak_memory', 0):.2f}",
        ])
    data.tables["solver_table"] = (comp_headers, comp_rows)

    # --- Table: detailed results ---
    det_headers = ["Problem", "Solver", "Status", "Objective", "Time (s)",
                   "Memory (MB)", "Iterations"]
    det_rows = []
    for r in runner.results:
        obj_val = r.solution.objective_value
        det_rows.append([
            r.problem_name,
            r.solver_name,
            r.solution.status,
            f"{obj_val:.4f}" if obj_val is not None else "N/A",
            f"{r.solve_time:.4f}",
            f"{r.memory_used_mb:.2f}",
            str(r.solution.iterations),
        ])
    data.tables["detailed_table"] = (det_headers, det_rows)

    # --- Table: friedman (if available) ---
    friedman_headers = ["Statistic", "Value"]
    friedman_rows = []
    try:
        from src.analysis.statistics import friedman_test
        import numpy as np
        perf_matrix = _build_performance_matrix(runner, solvers)
        if perf_matrix.shape[0] > 1 and perf_matrix.shape[1] > 1:
            f_results = friedman_test(perf_matrix)
            friedman_rows = [
                ["Friedman Q", f"{f_results.get('statistic', 0):.4f}"],
                ["p-value", f"{f_results.get('p_value', 0):.6f}"],
                ["Degrees of Freedom", str(f_results.get('df', 0))],
            ]
            avg_ranks = f_results.get("avg_ranks", [])
            for i, s_name in enumerate(solvers):
                if i < len(avg_ranks):
                    friedman_rows.append([f"Rank - {s_name}", f"{avg_ranks[i]:.4f}"])
    except Exception:
        friedman_rows = [["N/A", "Could not compute Friedman test"]]
    data.tables["friedman_table"] = (friedman_headers, friedman_rows)

    # --- Table: nemenyi (if available) ---
    nemenyi_headers = ["Solver Pair", "Rank Difference", "CD", "Significant"]
    nemenyi_rows = []
    try:
        if friedman_rows and len(friedman_rows) > 3:
            avg_ranks_list = []
            for r in friedman_rows[3:]:
                try:
                    avg_ranks_list.append(float(r[1]))
                except (ValueError, IndexError):
                    pass
            if len(avg_ranks_list) == len(solvers) and len(solvers) > 1:
                from src.analysis.statistics import nemenyi_posthoc
                avg_ranks_array = np.array(avg_ranks_list)
                n_results = nemenyi_posthoc(avg_ranks_array, num_problems)
                cd_val = n_results.get("critical_difference", 0)
                matrix = n_results.get("matrix", [])
                labels = n_results.get("solver_labels", solvers)
                for i in range(len(labels)):
                    for j in range(i + 1, len(labels)):
                        diff = matrix[i][j] if i < len(matrix) and j < len(matrix[i]) else 0
                        nemenyi_rows.append([
                            f"{labels[i]} vs {labels[j]}",
                            f"{diff:.4f}",
                            f"{cd_val:.4f}",
                            "Yes" if diff > cd_val else "No",
                        ])
    except Exception:
        nemenyi_rows = [["N/A", "N/A", "N/A", "N/A"]]
    data.tables["nemenyi_table"] = (nemenyi_headers, nemenyi_rows)

    # --- Images ---
    for name, path in chart_paths.items():
        if path:
            data.images[name] = path

    return data


def adapt_multi_problem(
    results: list[ProblemResult],
    solver_name: str,
    system_info: Optional[dict[str, Any]] = None,
    author: str = "",
) -> ReportData:
    """Convert multi-problem results into report data.

    Args:
        results: List of ProblemResult from solving multiple problems.
        solver_name: Name of the solver used.
        system_info: Optional system information.
        author: Report author name.

    Returns:
        ReportData for multi_report.csv template.
    """
    data = ReportData()
    total = len(results)
    solved = sum(1 for r in results if r.solution.is_optimal())
    failed = total - solved

    data.variables = {
        "solver_name": solver_name,
        "num_problems": total,
        "solved": solved,
        "failed": failed,
        "author": author or "Operations Research Laboratory",
        "author_label": f"Prepared by: {author}" if author else "Operations Research Laboratory",
        "summary_text": f"Problemas resueltos: {solved}/{total} utilizando {solver_name}.",
        "timestamp": system_info.get("timestamp", datetime.now().isoformat()) if system_info else "",
    }

    # --- Table: summary ---
    summary_headers = ["Problem", "Status", "Objective", "Time (s)", "Variables"]
    summary_rows = []
    for i, r in enumerate(results, 1):
        obj_val = r.solution.objective_value
        summary_rows.append([
            f"Problem {i}",
            r.solution.status,
            f"{obj_val:.4f}" if obj_val is not None else "N/A",
            f"{r.solve_time:.4f}",
            str(len(r.problem.variables)),
        ])
    data.tables["summary_table"] = (summary_headers, summary_rows)

    return data


# --- Internal helpers ---

def _build_problem_data_text(problem: LinearProblem) -> str:
    """Build a human-readable summary of problem data."""
    lines = [f"Variables: {len(problem.variables)}", f"Constraints: {len(problem.constraints)}"]
    if problem.variables:
        var_list = ", ".join(problem.variables)
        lines.append(f"Variable names: {var_list}")
    bound_lines = []
    for var in problem.variables:
        bound = problem.bounds.get(var)
        if bound:
            bound_lines.append(f"  {_format_bound(var, bound)}")
    if bound_lines:
        lines.append("Bounds:")
        lines.extend(bound_lines)
    return "\n".join(lines)


def _compute_slack(constraint: Any, solution: Solution) -> Optional[float]:
    """Compute slack for a constraint at the given solution.

    Slack = RHS - LHS for <= constraints
    Slack = LHS - RHS for >= constraints
    Slack = 0 for = constraints (if satisfied)
    """
    lhs = 0.0
    for var, coeff in constraint.coefficients.items():
        val = solution.variables.get(var, 0.0)
        lhs += coeff * val
    if constraint.sense == "<=":
        return constraint.rhs - lhs
    elif constraint.sense == ">=":
        return lhs - constraint.rhs
    else:
        return 0.0 if abs(lhs - constraint.rhs) < 1e-6 else lhs - constraint.rhs


def _build_performance_matrix(runner: BenchmarkRunner, solvers: list[str]) -> Any:
    """Build a (n_problems, n_solvers) matrix of solve times.

    Falls back to a minimal matrix if data is insufficient.
    """
    import numpy as np

    by_problem: dict[str, dict[str, float]] = {}
    for r in runner.results:
        if r.problem_name not in by_problem:
            by_problem[r.problem_name] = {}
        by_problem[r.problem_name][r.solver_name] = r.solve_time

    problem_names = sorted(by_problem.keys())
    if not problem_names or not solvers:
        return np.zeros((0, 0))

    matrix = np.zeros((len(problem_names), len(solvers)))
    for i, pname in enumerate(problem_names):
        for j, sname in enumerate(solvers):
            val = by_problem[pname].get(sname, np.nan)
            matrix[i, j] = val if val is not None else np.nan

    mask = ~np.isnan(matrix).any(axis=1)
    return matrix[mask]
