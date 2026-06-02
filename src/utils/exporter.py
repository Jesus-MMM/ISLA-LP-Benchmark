"""
Exportador de problemas de PL a formato LP (CPLEX).
"""

from ..core import LinearProblem


def export_to_lp_format(problem: LinearProblem, problem_name: str = "LPProblem") -> str:
    """
    Exporta un problema de PL al formato LP (CPLEX).

    Formato:
    \\ Problem name:  {name}
    Minimize
      objective:  expr
    Subject To
      constraints
    Bounds
      bounds
    End

    Args:
        problem: LinearProblem - El problema a exportar.
        problem_name: str - Nombre del problema (default "LPProblem").

    Returns:
        str: Representación del problema en formato LP.
    """
    lines = []

    lines.append(f"\\ Problem name:  {problem_name}")

    direction = "Minimize" if problem.sense == "min" else "Maximize"
    lines.append(direction)
    lines.append("  objective:  " + _format_expression(problem.objective, problem.variables))
    lines.append("")

    lines.append("Subject To")
    for i, constraint in enumerate(problem.constraints):
        c_name = constraint.name or f"c{i+1}"
        expr = _format_expression(constraint.coefficients, problem.variables)
        sense = constraint.sense.replace("=", "=").replace("<=", "<").replace(">=", ">")
        lines.append(f"  {c_name}:  {expr} {sense} {constraint.rhs}")
    lines.append("")

    lines.append("Bounds")
    for var in problem.variables:
        bound = problem.bounds.get(var)
        if bound:
            if bound.lower is not None and bound.upper is not None:
                lines.append(f"  {bound.lower} <= {var} <= {bound.upper}")
            elif bound.lower is not None:
                lines.append(f"  {var} >= {bound.lower}")
            elif bound.upper is not None:
                lines.append(f"  {var} <= {bound.upper}")
        else:
            lines.append(f"  {var} >= 0")
    lines.append("")

    lines.append("End")

    return "\n".join(lines)


def _format_expression(coefficients: dict[str, float], variables: list[str]) -> str:
    """Formatea una expresión lineal."""
    terms = []
    for var in variables:
        coeff = coefficients.get(var, 0)
        if coeff == 0:
            continue
        if coeff == 1:
            terms.append(f"+ {var}")
        elif coeff == -1:
            terms.append(f"- {var}")
        elif coeff > 0:
            terms.append(f"+ {coeff:g} {var}")
        else:
            terms.append(f"- {abs(coeff):g} {var}")

    if not terms:
        return "0"

    expr = " ".join(terms)
    if expr.startswith("+ ") or expr.startswith("- "):
        expr = expr[2:]

    return expr


def export_to_lp_file(problem: LinearProblem, filepath: str, problem_name: str = "LPProblem") -> None:
    """
    Exporta un problema de PL a un archivo en formato LP.

    Args:
        problem: LinearProblem - El problema a exportar.
        filepath: str - Ruta del archivo de salida.
        problem_name: str - Nombre del problema.
    """
    content = export_to_lp_format(problem, problem_name)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def export_to_mps_format(problem: LinearProblem, problem_name: str = "LPProblem") -> str:
    """
    Exporta un problema de PL al formato MPS.

    Args:
        problem: LinearProblem - El problema a exportar.
        problem_name: str - Nombre del problema (default "LPProblem").

    Returns:
        str: Representación del problema en formato MPS.
    """
    lines = [f"NAME          {problem_name}", "ROWS"]

    obj_name = "OBJ"
    lines.append(f" N  {obj_name}")

    row_map: dict[str, str] = {}
    for i, c in enumerate(problem.constraints):
        c_name = c.name or f"C{i+1}"
        row_map[c_name] = c_name
        if c.sense == "<=":
            lines.append(f" L  {c_name}")
        elif c.sense == ">=":
            lines.append(f" G  {c_name}")
        else:
            lines.append(f" E  {c_name}")

    lines.append("COLUMNS")

    has_integer = any(
        vtype in ("integer", "binary")
        for vtype in problem.variable_types.values()
    )
    if has_integer:
        lines.append("    MARKER    'MARKER'                 'INTORG'")

    for var in problem.variables:
        coeff = problem.objective.get(var, 0)
        if coeff != 0:
            lines.append(f"    {var:<8s}  {obj_name:<8s}  {coeff:>12g}")

        for i, c in enumerate(problem.constraints):
            c_name = c.name or f"C{i+1}"
            c_coeff = c.coefficients.get(var, 0)
            if c_coeff != 0:
                lines.append(f"    {var:<8s}  {c_name:<8s}  {c_coeff:>12g}")

    if has_integer:
        lines.append("    MARKER    'MARKER'                 'INTEND'")

    lines.append("RHS")

    rhs_name = "RHS1"
    for i, c in enumerate(problem.constraints):
        c_name = c.name or f"C{i+1}"
        if c.rhs != 0:
            lines.append(f"    {rhs_name:<8s}  {c_name:<8s}  {c.rhs:>12g}")

    has_bounds = any(
        var in problem.bounds for var in problem.variables
    )
    if has_bounds:
        lines.append("BOUNDS")
        for var in problem.variables:
            vtype = problem.variable_types.get(var, "continuous")
            bound = problem.bounds.get(var)
            if bound is None:
                continue
            lo = bound.lower
            up = bound.upper

            if vtype == "binary":
                lines.append(f" BV BND       {var}")
            elif lo is None and up is None:
                lines.append(f" FR BND       {var}")
            elif lo is not None and up is not None and lo == up:
                lines.append(f" FX BND       {var}  {lo:>12g}")
            else:
                if lo is not None and lo != 0:
                    lines.append(f" LO BND       {var}  {lo:>12g}")
                elif lo is not None and lo == 0:
                    pass
                if up is not None:
                    lines.append(f" UP BND       {var}  {up:>12g}")

    lines.append("ENDATA")

    return "\n".join(lines)


def export_to_mps_file(problem: LinearProblem, filepath: str, problem_name: str = "LPProblem") -> None:
    """
    Exporta un problema de PL a un archivo en formato MPS.

    Args:
        problem: LinearProblem - El problema a exportar.
        filepath: str - Ruta del archivo de salida.
        problem_name: str - Nombre del problema.
    """
    content = export_to_mps_format(problem, problem_name)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
