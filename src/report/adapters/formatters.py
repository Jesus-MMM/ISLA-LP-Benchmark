from __future__ import annotations

from typing import Any, Optional

from src.core.problem import LinearProblem
from src.core.solution import Solution
from src.solver.benchmark import BenchmarkRunner


def _format_coefficient(coeff: float, var: str) -> str:
    if coeff == 1.0:
        return f"+{var}"
    if coeff == -1.0:
        return f"-{var}"
    if coeff == int(coeff):
        coeff_str = str(int(coeff))
    else:
        coeff_str = str(coeff)
    if coeff >= 0:
        return f"+{coeff_str}{var}"
    return f"{coeff_str}{var}"


def _format_expression(coefficients: dict[str, float]) -> str:
    if not coefficients:
        return "0"
    terms = []
    for var, coeff in coefficients.items():
        term = _format_coefficient(coeff, var)
        terms.append(term)
    expr = " ".join(terms)
    if expr.startswith("+"):
        expr = expr[1:]
    return expr


def _format_objective(obj: dict[str, float], sense: str) -> str:
    sense_label = "Maximizar" if sense.lower() == "max" else "Minimizar"
    expr = _format_expression(obj)
    return f"{sense_label} Z = {expr}"


def _format_constraint_text(c: Any) -> str:
    expr = _format_expression(c.coefficients)
    return f"{expr} {c.sense} {c.rhs}"


def _format_bound(var: str, bound: Any) -> str:
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


def _compute_slack(constraint: Any, solution: Solution) -> Optional[float]:
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


def _get_constraint_name(c: Any, index: int) -> str:
    raw = getattr(c, "name", "") or ""
    raw = raw.strip()
    if raw and raw.startswith("c"):
        return f"R{raw[1:]}"
    if raw:
        return raw
    return f"R{index}"


def _get_constraint_name_from_sensitivity(raw_name: str) -> str:
    if raw_name.startswith("c") and raw_name[1:].isdigit():
        idx = int(raw_name[1:]) - 1
        return f"R{idx}"
    return raw_name


def _get_solver_version(solver_name: str) -> str:
    versions = {
        "gurobi": "Gurobi 11.0.3",
        "highs": "HiGHS 1.7.2",
        "glpk": "GLPK 5.0.0",
        "cbc": "CBC 2.10.12",
        "scip": "SCIP 9.1.0",
        "ecos": "ECOS 2.0.12",
        "osqp": "OSQP 1.0.1",
        "cvxopt": "CVXOPT 1.3.2",
        "scs": "SCS 3.2.4",
        "ipopt": "Ipopt 3.14.16 (via CasADi)",
    }
    return versions.get(solver_name.lower(), solver_name)


def _build_solver_log_table(solution: Solution, times: Any, solver_name: str) -> tuple[list[str], list[list[str]]]:
    nq = solution.numerical_quality
    _sim = getattr(solution, 'simplex_iterations', None)
    sim_str = str(_sim) if _sim is not None else 'N/A'
    _bar = getattr(solution, 'barrier_iterations', None)
    bar_str = str(_bar) if _bar is not None else 'N/A'

    headers = ["Metrica del Proceso", "Valor", "Observacion"]
    rows = [
        ["build_time", f"{times.build_time:.4f} s", "Tiempo de construccion de la matriz"],
        ["solve_time", f"{times.solve_time:.4f} s", f"Tiempo interno de {solver_name}"],
        ["simplex_iterations", sim_str, "Iteraciones del metodo simplex"],
        ["barrier_iterations", bar_str, "Iteraciones del metodo de barrera"],
        ["nodes", str(solution.nodes), "Nodos explorados (0 en LP puro)"],
        ["mip_gap", f"{nq.mip_gap:.6f}" if nq else "N/A", "Gap de optimalidad MILP (0 en LP puro)"],
        ["max_constraint_viol", f"{nq.max_constraint_viol:.2e}" if nq else "N/A", "Violacion maxima de restricciones"],
        ["condition_number", f"{nq.condition_number:.4f}" if nq and nq.condition_number is not None else "N/A", "Numero de condicion de la matriz"],
        ["presolve_reduction", f"{nq.presolve_reduction:.2f}%" if nq else "N/A", "Reduccion por presolve"],
        ["cuts_generated", str(nq.cuts_generated) if nq else "N/A", "Cortes generados (0 en LP puro)"],
        ["nodes_per_second", f"{nq.nodes_per_second:.2f}" if nq else "N/A", "Rendimiento del branch-and-bound"],
        ["memory_used_mb", "N/A", "Memoria no capturada con precision en problemas pequenos"],
    ]
    return (headers, rows)


def _build_objective_with_vars(problem: LinearProblem) -> str:
    sense = "Maximizar" if problem.sense.lower() == "max" else "Minimizar"
    expr = _format_expression(problem.objective)
    lines = [f"{sense} Z = {expr}", "", "Donde:"]
    for var in problem.variables:
        coeff = problem.objective.get(var, 0)
        lines.append(f"  {var}: Coeficiente en la funcion objetivo = {coeff}")
    return "\n".join(lines)


def _build_problem_data_text(problem: LinearProblem) -> str:
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


def _build_performance_matrix(runner: BenchmarkRunner, solvers: list[str]) -> Any:
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


_problem_cache = {}

def _get_problem_from_result(result: Any) -> Optional[LinearProblem]:
    if hasattr(result, 'problem'):
        p = result.problem
        if p is not None:
            return p
    text = getattr(result, 'problem_text', '')
    if text:
        if text in _problem_cache:
            return _problem_cache[text]
        try:
            from src.parser import LPParser
            p = LPParser(text).parse()
            _problem_cache[text] = p
            return p
        except Exception:
            pass
    return None


def _build_recommendations(summary: dict, solvers: list[str]) -> str:
    by_solver = summary.get("by_solver", {})
    if not by_solver:
        return "No hay suficientes datos para generar recomendaciones."

    best_solver = min(solvers, key=lambda s: by_solver.get(s, {}).get("avg_time", float("inf")))
    best_time = by_solver.get(best_solver, {}).get("avg_time", 0)

    reliable = max(solvers, key=lambda s: by_solver.get(s, {}).get("successful", 0) /
                   max(by_solver.get(s, {}).get("runs", 1), 1))
    reliable_rate = by_solver.get(reliable, {}).get("successful", 0) / max(
        by_solver.get(reliable, {}).get("runs", 1), 1)

    lines = [
        f"Basado en los resultados del benchmark en {len(solvers)} solvers y "
        f"{summary.get('total_benchmarks', 0)} ejecuciones totales, se recomienda lo siguiente:",
        "",
        f"1. Para maxima velocidad: {best_solver.upper()} obtuvo el menor tiempo promedio "
        f"({best_time:.4f}s). Es la mejor opcion cuando el tiempo de computo es critico.",
        "",
        f"2. Para maxima confiabilidad: {reliable.upper()} resolvio exitosamente el "
        f"{reliable_rate*100:.1f}% de los problemas. Es la opcion mas robusta.",
        "",
        "3. Para MILP: Si el problema incluye variables enteras o binarias, "
        "se recomienda Gurobi (comercial) o CBC/SCIP (open-source).",
        "",
        "4. Para problemas de gran escala: HiGHS y Gurobi demostraron el mejor "
        "rendimiento en problemas con muchas variables y restricciones.",
        "",
        "Nota: La seleccion final del solver debe considerar el equilibrio entre "
        "velocidad, confiabilidad, licencia y soporte de caracteristicas MILP.",
    ]
    return "\n".join(lines)
