from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ProgressPoint:
    """Punto de progreso durante la resolución."""
    iteration: int
    time: float
    objective: float
    gap: float = 0.0
    nodes: int = 0


@dataclass
class NumericalQuality:
    """Métricas de calidad numérica y MILP."""
    max_bound_viol: float = 0.0
    max_constraint_viol: float = 0.0
    condition_number: Optional[float] = None
    mip_gap: float = 0.0
    first_feasible_time: float = 0.0
    nodes_per_second: float = 0.0
    cuts_generated: int = 0
    presolve_reduction: float = 0.0


@dataclass
class Solution:
    """
    Representa la solución de un problema de programación lineal (LP/MILP).
    
    ### Atributos:
    - status: str - Estado de la solución (OPTIMAL, INFEASIBLE, UNBOUNDED, etc.)
    - objective_value: float | None - Valor de la función objetivo en el óptimo.
    - variables: dict[str, float] - Valores de las variables de decisión.
    - dual_values: dict[str, float] - Precios sombra para restricciones (opcional).
    - reduced_costs: dict[str, float] - Costos reducidos para variables (opcional).
    - iterations: int - Número de iteraciones del simplex (opcional).
    - nodes: int - Número de nodos branch-and-bound (opcional).
    - sensitivity: Optional[SensitivityInfo] - Rangos de sensibilidad.
    - iis: Optional[list[str]] - Lista de restricciones/bounds del IIS.
    - basis: Optional[dict[str, str]] - Estado de la base {var: "basic"/"nonbasic"}.
    - progress_log: Optional[list[ProgressPoint]] - Log de progreso.
    - numerical_quality: Optional[NumericalQuality] - Calidad numérica.
    """
    status: str
    objective_value: Optional[float]
    variables: dict[str, float]
    dual_values: Optional[dict[str, float]] = None
    reduced_costs: Optional[dict[str, float]] = None
    iterations: int = 0
    nodes: int = 0
    # NUEVOS CAMPOS PARA MILP Y SENSIBILIDAD
    sensitivity: Optional[Any] = None
    iis: Optional[list[str]] = None
    basis: Optional[dict[str, str]] = None
    progress_log: Optional[list[ProgressPoint]] = None
    numerical_quality: Optional[NumericalQuality] = None

    def is_optimal(self) -> bool:
        """Verifica si la solucion es optima usando tolerancia."""
        status_upper = self.status.strip().upper()
        return status_upper == "OPTIMAL" or status_upper == "OPTIMAL (TOLERANCE)" or "OPTIMAL" in status_upper

    def is_infeasible(self) -> bool:
        """Verifica si el problema es infactible."""
        return self.status == "INFEASIBLE"

    def is_unbounded(self) -> bool:
        """Verifica si el problema es no acotado."""
        return self.status == "UNBOUNDED"

    def has_errors(self) -> bool:
        """Verifica si hubo un error durante la resolución."""
        return self.status.startswith("ERROR")

    def print_summary(self, verbose: bool = False) -> str:
        """
        Genera un resumen formateado de la solución.
        
        Args:
            verbose: Si es True, incluye valores duales y costos reducidos.
        
        Returns:
            str: Cadena formateada con el resumen de la solución.
        """
        lines = []
        lines.append(f"Estado: {self.status}")

        if self.objective_value is not None:
            lines.append(f"Valor objetivo: {self.objective_value:.4f}")

        if self.variables:
            lines.append("Variables:")
            for var, value in sorted(self.variables.items()):
                lines.append(f"  {var} = {value:.4f}")

        if verbose:
            if self.reduced_costs:
                lines.append("Costos reducidos:")
                for var, cost in sorted(self.reduced_costs.items()):
                    lines.append(f"  {var}: {cost:.4f}")

            if self.dual_values:
                lines.append("Precios sombra (dual):")
                for constr, price in sorted(self.dual_values.items()):
                    lines.append(f"  {constr}: {price:.4f}")

            if self.iterations > 0:
                lines.append(f"Iteraciones: {self.iterations}")
            if self.nodes > 0:
                lines.append(f"Nodos: {self.nodes}")

        return "\n".join(lines)

    def __str__(self) -> str:
        """Representación en cadena de la solución."""
        if self.status == "OPTIMAL" and self.objective_value is not None:
            vars_str = ", ".join(
                f"{k}={v:.2f}" for k, v in sorted(self.variables.items())
            )
            return f"OPTIMAL: Z={self.objective_value:.4f} ({vars_str})"
        return f"{self.status}"


@dataclass
class SolutionTable:
    """Representación tabular unificada de la solución usando Polars."""
    variables: Any = None  # pl.DataFrame: variable, value, type, lower_bound, upper_bound, reduced_cost
    constraints: Any = None  # pl.DataFrame: name, lhs, rhs, sense, slack, dual_value
    objective_terms: Any = None  # pl.DataFrame: term, coefficient, variable_value, contribution
    sensitivity: Any = None  # pl.DataFrame: variable/constraint, current, min, max
    iis: Optional[list[str]] = None
    basis: Any = None  # pl.DataFrame: variable, status


def to_solution_table(solution: Solution, problem: Any) -> SolutionTable:
    """Convierte una Solution en SolutionTable (tabular)."""
    import polars as pl
    from .problem import LinearProblem as LP
    
    if not isinstance(problem, LP):
        return SolutionTable()
    
    # Variables table
    var_data = []
    for var, value in solution.variables.items():
        bound = problem.bounds.get(var)
        lb = bound.lower if bound else None
        ub = bound.upper if bound else None
        vtype = problem.variable_types.get(var, "continuous")
        rc = solution.reduced_costs.get(var) if solution.reduced_costs else None
        var_data.append({
            "variable": var,
            "value": value,
            "type": vtype,
            "lower_bound": lb,
            "upper_bound": ub,
            "reduced_cost": rc
        })
    variables_df = pl.DataFrame(var_data) if var_data else pl.DataFrame()
    
    # Constraints table
    constr_data = []
    for i, constr in enumerate(problem.constraints):
        lhs = sum(
            coeff * solution.variables.get(var, 0.0)
            for var, coeff in constr.coefficients.items()
        )
        slack = constr.rhs - lhs if constr.sense == "<=" else (
            lhs - constr.rhs if constr.sense == ">=" else abs(lhs - constr.rhs)
        )
        dual = solution.dual_values.get(constr.name or f"R{i}") if solution.dual_values else None
        constr_data.append({
            "name": constr.name or f"R{i}",
            "lhs": lhs,
            "rhs": constr.rhs,
            "sense": constr.sense,
            "slack": slack,
            "dual_value": dual
        })
    constraints_df = pl.DataFrame(constr_data) if constr_data else pl.DataFrame()
    
    # Objective terms
    obj_data = []
    for var, coeff in problem.objective.items():
        value = solution.variables.get(var, 0.0)
        obj_data.append({
            "term": var,
            "coefficient": coeff,
            "variable_value": value,
            "contribution": coeff * value
        })
    objective_terms_df = pl.DataFrame(obj_data) if obj_data else pl.DataFrame()
    
    return SolutionTable(
        variables=variables_df,
        constraints=constraints_df,
        objective_terms=objective_terms_df,
        iis=solution.iis
    )
