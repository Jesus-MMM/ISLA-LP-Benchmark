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