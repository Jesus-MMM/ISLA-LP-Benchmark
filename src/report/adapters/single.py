from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from src.core.problem import LinearProblem
from src.core.solution import Solution
from src.analysis.analysis import ExecutionTimes
from src.report.adapters.types import ReportData
from src.report.adapters.formatters import (
    _format_expression,
    _format_objective,
    _get_constraint_name,
    _get_constraint_name_from_sensitivity,
    _build_solver_log_table,
    _build_objective_with_vars,
    _build_problem_data_text,
)


def adapt_single_solution(
    problem: LinearProblem,
    solution: Solution,
    times: ExecutionTimes,
    system_info: dict[str, Any],
    solver_name: str,
    solver_config: Optional[dict[str, Any]] = None,
    feasible_region_path: Optional[str] = None,
    objective_progression_path: Optional[str] = None,
    solver_log: Optional[str] = None,
    author: str = "",
    institution_name: str = "",
    abstract_text: str = "",
    keywords_text: str = "",
    problem_file_hash: Optional[str] = None,
    executive_interpretation: Optional[str] = None,
    problem_description: str = "",
) -> ReportData:
    data = ReportData()
    plat = system_info.get("platform", {})
    has_charts = feasible_region_path is not None

    sense_label = "Maximizacion" if problem.sense.lower() == "max" else "Minimizacion"
    is_milp = any(
        t in ("integer", "binary") for t in problem.variable_types.values()
    )
    problem_type = "MILP" if is_milp else "LP"
    total_time_s = times.parse_time + times.build_time + times.solve_time
    obj_val = solution.objective_value
    obj_val_str = f"{obj_val:,.4f}" if obj_val is not None else "N/A"
    obj_val_int = f"{int(obj_val):,}" if obj_val is not None and obj_val == int(obj_val) else obj_val_str

    is_optimal = solution.is_optimal()

    var_descriptions = {}
    for i, var in enumerate(problem.variables):
        var_descriptions[var] = f"Variable de decision {chr(65 + i)}"

    if is_optimal:
        v_lines = ["**Factibilidad:** Comprobada matematicamente."]
        for i, c in enumerate(problem.constraints):
            lhs_val = sum(
                coeff * solution.variables.get(var, 0.0)
                for var, coeff in c.coefficients.items()
            )
            expr = _format_expression(c.coefficients)
            name = _get_constraint_name(c, i)
            v_lines.append(
                f"  - {name}: {expr} = {lhs_val:.2f} {c.sense} {c.rhs}. "
                f"{'Cumple' if abs(lhs_val - c.rhs) < 1e-6 or (c.sense == '<=' and lhs_val <= c.rhs + 1e-6) or (c.sense == '>=' and lhs_val >= c.rhs - 1e-6) else 'No cumple'}"
            )
        v_feas = "\n".join(v_lines)
        v_opt = "**Optimalidad:** Verificada por el solver. No existe una solucion factible con mejor valor objetivo dentro de la region factible."
        v_slack = "**Holguras Complementarias:** Verificado. Si la holgura es cero, el precio sombra es positivo; si la holgura es positiva, el precio sombra es cero (teorema de holguras complementarias)."
    else:
        v_feas = "**Factibilidad:** No - El problema no tiene solucion factible."
        v_opt = "**Optimalidad:** N/A - El problema no es optimo."
        v_slack = "**Holguras:** N/A - No aplica."

    if executive_interpretation is None and is_optimal:
        var_desc = ", ".join(
            f"{k} = {v:.2f}" for k, v in sorted(solution.variables.items())
        )
        if problem.sense.lower() == "max":
            exec_text = (
                f"La solucion optima encontrada tiene un valor de Z = {obj_val_str}. "
                f"Las variables de decision en sus valores optimos son: {var_desc}. "
                "Esta combinacion maximiza la funcion objetivo respetando "
                "todas las restricciones impuestas."
            )
            if len(solution.variables) == 2:
                exec_text += (
                    " Ambos recursos se consumen en su totalidad (holgura cero), "
                    "lo que indica que el sistema esta al limite de su capacidad actual. "
                    "Para incrementar la produccion, se requieren unidades adicionales de los recursos limitantes."
                )
        else:
            exec_text = (
                f"La solucion optima encontrada tiene un valor de Z = {obj_val_str}. "
                f"Las variables de decision en sus valores optimos son: {var_desc}. "
                "Esta combinacion minimiza la funcion objetivo respetando "
                "todas las restricciones impuestas."
            )
    else:
        exec_text = executive_interpretation or "No hay interpretacion disponible."

    ref_simplex = "Dantzig, G. B. (1947). Maximization of a linear function of variables subject to linear inequalities. Activity Analysis of Production and Allocation."
    ref_interior = "Karmarkar, N. (1984). A new polynomial-time algorithm for linear programming. Combinatorica, 4(4), 373-395."
    ref_duality = "Bazaraa, M. S., Jarvis, J. J., & Sherali, H. D. (2010). Linear Programming and Network Flows (4th ed.). Wiley."
    if is_milp:
        ref_milp = "Land, A. H. & Doig, A. G. (1960). An automatic method of solving discrete programming problems. Econometrica, 28(3), 497-520."
    else:
        ref_milp = ""
    ref_solver = f"{solver_name.upper()} Optimization. (2026). Reference Manual. Disponible en: https://{solver_name}.com/documentation"

    solver_log_headers, solver_log_rows = _build_solver_log_table(solution, times, solver_name)
    data.tables["solver_log_table"] = (solver_log_headers, solver_log_rows)

    sens_text_obj = ""
    sens_text_rhs = ""
    sens = solution.sensitivity
    if sens and is_optimal:
        if hasattr(sens, "objective_ranges") and sens.objective_ranges:
            parts = []
            for sr in sens.objective_ranges:
                lo_str = f"{sr.lower:.2f}" if sr.lower is not None else "-inf"
                up_str = f"{sr.upper:.2f}" if sr.upper is not None else "+inf"
                parts.append(
                    f"{sr.name}: [{lo_str}, {up_str}]"
                )
            sens_text_obj = (
                "Los coeficientes de la funcion objetivo pueden variar dentro de los rangos "
                "indicados sin que cambie la base optima. Fuera de estos rangos, la estrategia "
                f"de produccion (valores de las variables) se modificaria. Rangos: {'; '.join(parts)}."
            )
        if hasattr(sens, "rhs_ranges") and sens.rhs_ranges:
            parts = []
            for sr in sens.rhs_ranges:
                lo_str = f"{sr.lower:.2f}" if sr.lower is not None else "-inf"
                up_str = f"{sr.upper:.2f}" if sr.upper is not None else "+inf"
                parts.append(
                    f"{_get_constraint_name_from_sensitivity(sr.name)}: [{lo_str}, {up_str}]"
                )
            sens_text_rhs = (
                "Los lados derechos (RHS) de las restricciones pueden variar dentro de los rangos "
                "senalados sin que cambien los precios sombra. Esto define el intervalo de validez "
                "del analisis de sensibilidad. Rangos: " + "; ".join(parts) + "."
            )

    data.variables = {
        "solver_name": solver_name,
        "status": solution.status,
        "objective_value": obj_val_str,
        "objective_value_int": obj_val_int,
        "num_variables": len(problem.variables),
        "num_constraints": len(problem.constraints),
        "problem_type": problem_type,
        "problem_name": system_info.get("problem_name", "unknown"),
        "problem_description": problem_description or (
            "Problema de optimizacion lineal. "
            "Consulte las restricciones y la funcion objetivo para los detalles del modelo."
        ),
        "problem_hash": problem_file_hash or "N/A",
        "parse_time_ms": f"{times.parse_time * 1000:.2f}",
        "build_time_ms": f"{times.build_time * 1000:.2f}",
        "solve_time_ms": f"{times.solve_time * 1000:.2f}",
        "total_time_ms": f"{total_time_s * 1000:.2f}",
        "total_time_s": f"{total_time_s:.4f}",
        "system_os": f"{plat.get('system', '?')} {plat.get('release', '?')}",
        "system_python": plat.get("python_version", "?"),
        "hostname": system_info.get("hostname", "?"),
        "timestamp": system_info.get("timestamp", datetime.now().isoformat()),
        "author": author or "Operations Research Laboratory",
        "author_name": author or "Operations Research Laboratory",
        "author_label": f"Prepared by: {author}" if author else "Operations Research Laboratory",
        "institution_name": institution_name or "Instituto de Investigacion Operativa",
        "abstract_text": abstract_text or "Este informe presenta los resultados de la optimizacion de un problema de Programacion Lineal (LP).",
        "keywords_text": keywords_text or "optimizacion, programacion lineal, investigacion operativa",
        "problem_data_text": _build_problem_data_text(problem),
        "objective_text": _format_objective(problem.objective, problem.sense),
        "objective_formatted": _build_objective_with_vars(problem),
        "has_feasible_region": has_charts,
        "feasible_region_path": (feasible_region_path.replace("\\", "/") if feasible_region_path else ""),
        "objective_progression_path": (objective_progression_path.replace("\\", "/") if objective_progression_path else ""),
        "validation_feasible": v_feas,
        "validation_optimal": v_opt,
        "validation_slacks": v_slack,
        "executive_interpretation": exec_text,
        "sensitivity_obj_interpretation": sens_text_obj,
        "sensitivity_rhs_interpretation": sens_text_rhs,
        "ref_simplex": ref_simplex,
        "ref_duality": ref_duality,
        "ref_milp": ref_milp,
        "ref_interior_point": ref_interior,
        "ref_solver_doc": ref_solver,
        "sense_label": sense_label,
        "sense_label_lower": sense_label.lower(),
        "problem_type_label": problem_type,
        "input_format": system_info.get("input_format", ".txt"),
        "optimization_direction": problem.sense.upper(),
        "has_milp_references": str(is_milp).lower(),
    }

    exec_headers = ["Metrica", "Valor"]
    exec_rows = [
        ["Estado", solution.status],
        ["Valor Optimo (Z*)", obj_val_str],
        ["Tiempo Total", f"{total_time_s:.4f} s"],
        ["Solver", solver_name],
        ["Tipo de Problema", problem_type],
        ["Tipo de Optimizacion", problem.sense.upper()],
        ["Variables", str(len(problem.variables))],
        ["Restricciones", str(len(problem.constraints))],
    ]
    data.tables["executive_table"] = (exec_headers, exec_rows)

    meta_headers = ["Atributo", "Valor"]
    meta_rows = [
        ["Archivo de Origen", system_info.get("problem_name", "N/A")],
        ["Formato de Entrada", system_info.get("input_format", ".txt")],
        ["Tipo de Problema", problem_type],
        ["Direccion de Optimizacion", problem.sense.upper()],
        ["Numero de Variables", str(len(problem.variables))],
        ["Numero de Restricciones", str(len(problem.constraints))],
        ["Hash SHA256", problem_file_hash or "N/A"],
    ]
    data.tables["problem_metadata_table"] = (meta_headers, meta_rows)

    constraint_headers = ["ID Restriccion", "LHS (Lado Izquierdo)", "Sentido", "RHS (Lado Derecho)", "Descripcion"]
    constraint_rows = []
    for i, c in enumerate(problem.constraints):
        name = _get_constraint_name(c, i)
        constraint_rows.append([
            name,
            _format_expression(c.coefficients),
            c.sense,
            str(c.rhs),
            f"Restriccion {name} del modelo",
        ])
    data.tables["constraints_table"] = (constraint_headers, constraint_rows)

    sol_headers = ["Variable", "Valor Optimo", "Descripcion"]
    sol_rows = []
    for var in problem.variables:
        val = solution.variables.get(var, 0.0)
        val_str = f"{int(val)}" if val == int(val) else f"{val:.4f}"
        sol_rows.append([var, val_str, var_descriptions.get(var, "")])
    data.tables["solution_table"] = (sol_headers, sol_rows)

    slack_headers = ["Restriccion", "RHS", "Holgura (Slack)", "Precio Sombra (Dual)", "Estatus", "Interpretacion"]
    slack_rows = []
    for i, c in enumerate(problem.constraints):
        name = _get_constraint_name(c, i)
        lhs = sum(
            coeff * solution.variables.get(var, 0.0)
            for var, coeff in c.coefficients.items()
        )
        if c.sense == "<=":
            slack = c.rhs - lhs
        elif c.sense == ">=":
            slack = lhs - c.rhs
        else:
            slack = 0.0 if abs(lhs - c.rhs) < 1e-6 else lhs - c.rhs

        dual = None
        if solution.dual_values:
            for candidate in [name, f"c{i+1}", f"R{i}", f"r{i}", f"c{i}"]:
                if candidate in solution.dual_values:
                    dual = solution.dual_values[candidate]
                    break
            if dual is None and i < len(solution.dual_values):
                try:
                    vals = list(solution.dual_values.values())
                    if i < len(vals):
                        dual = vals[i]
                except Exception:
                    pass

        dual_str = f"{dual:.4f}" if dual is not None else "N/A"
        is_active = "Activa" if abs(slack) < 1e-6 else "Inactiva"

        if abs(slack) < 1e-6 and dual is not None:
            interp = f"Por cada unidad adicional de RHS, Z* cambia en {dual:.2f}"
        elif abs(slack) < 1e-6 and dual is None:
            interp = "Restriccion activa. Precio sombra no disponible."
        else:
            interp = f"Holgura de {slack:.2f} unidades. Recurso no escaso."

        slack_rows.append([
            name,
            str(c.rhs),
            f"{slack:.4f}",
            dual_str,
            is_active,
            interp,
        ])
    data.tables["slack_table"] = (slack_headers, slack_rows)

    rc_headers = ["Variable", "Valor", "Costo Reducido", "Interpretacion"]
    rc_rows = []
    for var in problem.variables:
        val = solution.variables.get(var, 0.0)
        rc = solution.reduced_costs.get(var, 0.0) if solution.reduced_costs else 0.0
        if abs(val) > 1e-6:
            interp = "Variable en la base. Costo reducido cero por definicion."
        elif rc > 0:
            interp = f"El coeficiente debe mejorar en {rc:.2f} para que la variable entre a la base."
        else:
            interp = "Variable no basica sin presion de entrada."
        rc_rows.append([var, f"{val:.4f}", f"{rc:.4f}", interp])
    data.tables["reduced_cost_table"] = (rc_headers, rc_rows)

    config = solver_config or {}
    config_headers = ["Parametro", "Valor Configurado", "Nota"]
    is_lp = not is_milp
    config_rows = [
        ["Solver", solver_name, ""],
        ["TimeLimit", str(config.get("time_limit", "Predeterminado")), ""],
        ["Presolve", str(config.get("presolve", "Auto")), ""],
        ["MIPGap", str(config.get("mip_gap", "1e-4")), "Aplicable solo en MILP. En LP puro el solver lo ignora y garantiza optimalidad exacta." if is_lp else ""],
        ["Threads", str(config.get("threads", "Auto")), ""],
        ["Verbose", str(config.get("verbose", "False")), ""],
    ]
    data.tables["solver_config_table"] = (config_headers, config_rows)

    basis_headers = ["Tipo de Entidad", "Nombre", "Categoria"]
    basis_rows = []
    if solution.basis:
        for var, category in solution.basis.items():
            basis_rows.append(["Variable", var, category])
    else:
        for var in problem.variables:
            val = solution.variables.get(var, 0.0)
            cat = "Basica" if abs(val) > 1e-6 else "No Basica"
            basis_rows.append(["Variable", var, cat])
    data.tables["basis_table"] = (basis_headers, basis_rows)

    nq = solution.numerical_quality
    metrics_headers = ["Metrica", "Valor", "Observacion"]
    sim_iter = getattr(solution, 'simplex_iterations', None) or 'N/A'
    bar_iter = getattr(solution, 'barrier_iterations', None) or 'N/A'
    metrics_rows = [
        ["solve_time (s)", f"{times.solve_time:.4f}", f"Tiempo interno del solver {solver_name}"],
        ["iterations", str(solution.iterations), "Iteraciones totales del algoritmo"],
        ["simplex_iterations", str(sim_iter), "Iteraciones del metodo simplex (N/A si se uso barrera)"],
        ["barrier_iterations", str(bar_iter), "Iteraciones del metodo de barrera (N/A si se uso simplex)"],
        ["nodes", str(solution.nodes), "Nodos explorados en B&B (0 en LP puro)"],
        ["mip_gap", f"{nq.mip_gap:.6f}" if nq else "N/A", "Gap de optimalidad MILP (0 en LP puro)"],
        ["presolve_reduction (%)", f"{nq.presolve_reduction:.2f}" if nq else "N/A", "Porcentaje de reduccion por presolve"],
        ["cuts_generated", str(nq.cuts_generated) if nq else "N/A", "Cortes generados (0 en LP puro)"],
        ["nodes_per_second", f"{nq.nodes_per_second:.2f}" if nq else "N/A", "Rendimiento del branch-and-bound"],
    ]
    data.tables["metrics_table"] = (metrics_headers, metrics_rows)

    sens_obj_headers = ["Variable", "Coef Actual", "Limite Inferior", "Limite Superior", "Interpretacion"]
    sens_obj_rows = []
    if sens and hasattr(sens, "objective_ranges"):
        for sr in sens.objective_ranges:
            lo = f"{sr.lower:.4f}" if sr.lower is not None else "-inf"
            up = f"{sr.upper:.4f}" if sr.upper is not None else "+inf"
            if sr.lower is not None and sr.upper is not None:
                interp = f"El coeficiente puede variar entre {lo} y {up} sin cambiar la base optima"
            elif sr.lower is not None:
                interp = f"El coeficiente no tiene cota superior. Cota inferior: {lo}"
            elif sr.upper is not None:
                interp = f"El coeficiente no tiene cota inferior. Cota superior: {up}"
            else:
                interp = "No hay restricciones de sensibilidad para esta variable"
            sens_obj_rows.append([sr.name, f"{sr.current:.4f}", lo, up, interp])
    if not sens_obj_rows:
        sens_obj_rows.append(["N/A", "N/A", "N/A", "N/A", "No hay datos de sensibilidad disponibles"])
    data.tables["sensitivity_obj_table"] = (sens_obj_headers, sens_obj_rows)

    sens_rhs_headers = ["Restriccion", "RHS Actual", "Limite Inferior", "Limite Superior", "Interpretacion"]
    sens_rhs_rows = []
    if sens and hasattr(sens, "rhs_ranges"):
        for sr in sens.rhs_ranges:
            name_norm = _get_constraint_name_from_sensitivity(sr.name)
            lo = f"{sr.lower:.4f}" if sr.lower is not None else "-inf"
            up = f"{sr.upper:.4f}" if sr.upper is not None else "+inf"
            if sr.lower is not None and sr.upper is not None:
                interp = f"El RHS puede variar entre {lo} y {up} sin que cambien los precios sombra"
            elif sr.lower is not None:
                interp = f"El RHS no tiene cota superior. Cota inferior: {lo}"
            elif sr.upper is not None:
                interp = f"El RHS no tiene cota inferior. Cota superior: {up}"
            else:
                interp = "No hay restricciones de sensibilidad para esta restriccion"
            sens_rhs_rows.append([name_norm, f"{sr.current:.4f}", lo, up, interp])
    if not sens_rhs_rows:
        sens_rhs_rows.append(["N/A", "N/A", "N/A", "N/A", "No hay datos de sensibilidad disponibles"])
    data.tables["sensitivity_rhs_table"] = (sens_rhs_headers, sens_rhs_rows)

    if has_charts:
        data.images["feasible_region"] = feasible_region_path

    return data
