"""
Analisis de sensibilidad para problemas de programacion lineal.
Proporciona rangos de sensibilidad para coeficientes objetivo,
lados derechos de restricciones, y costos reducidos.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SensitivityRange:
    """
    Rango de sensibilidad para un coeficiente o lado derecho.

    ### Atributos:
    - name: str - Nombre de la variable o restriccion.
    - current: float - Valor actual del coeficiente o RHS.
    - lower: float | None - Limite inferior del rango.
    - upper: float | None - Limite superior del rango.
    - reduced_cost: float | None - Costo reducido asociado.
    - dual_value: float | None - Valor dual asociado.
    """
    name: str
    current: float
    lower: float | None = None
    upper: float | None = None
    reduced_cost: float | None = None
    dual_value: float | None = None


@dataclass
class SensitivityAnalysis:
    """
    Resultado completo del analisis de sensibilidad.

    ### Atributos:
    - objective_ranges: list[SensitivityRange] - Rangos para coeficientes objetivo.
    - rhs_ranges: list[SensitivityRange] - Rangos para lados derechos de restricciones.
    - bound_ranges: list[SensitivityRange] - Rangos para limites de variables.
    """
    objective_ranges: list[SensitivityRange] = field(default_factory=list)
    rhs_ranges: list[SensitivityRange] = field(default_factory=list)
    bound_ranges: list[SensitivityRange] = field(default_factory=list)

    def get_objective_range(self, name: str) -> SensitivityRange | None:
        """Obtiene el rango de sensibilidad para una variable objetivo."""
        for r in self.objective_ranges:
            if r.name == name:
                return r
        return None

    def get_rhs_range(self, name: str) -> SensitivityRange | None:
        """Obtiene el rango de sensibilidad para una restriccion."""
        for r in self.rhs_ranges:
            if r.name == name:
                return r
        return None


def extract_highs_sensitivity(hp: Any) -> SensitivityAnalysis | None:
    """
    Extrae analisis de sensibilidad de un modelo HiGHS resuelto.

    HiGHS no tiene API de ranging nativa via highspy, por lo que
    se estiman rangos basados en costos reducidos y valores duales.
    """
    if hp is None:
        return None

    try:
        solution = hp.getSolution()

        if solution is None:
            return None

        num_cols = hp.getNumCol()
        num_rows = hp.getNumRow()

        objective_ranges: list[SensitivityRange] = []
        rhs_ranges: list[SensitivityRange] = []

        col_values = solution.col_value if hasattr(solution, 'col_value') else []
        row_dual = solution.row_dual if hasattr(solution, 'row_dual') else []

        for i in range(num_cols):
            col_info = hp.getColsByRange(i, i + 1) if hasattr(hp, 'getColsByRange') else None
            cost = col_info.cost[0] if col_info and hasattr(col_info, 'cost') and len(col_info.cost) > 0 else 0.0
            lower = col_info.lower[0] if col_info and hasattr(col_info, 'lower') and len(col_info.lower) > 0 else None
            upper = col_info.upper[0] if col_info and hasattr(col_info, 'upper') and len(col_info.upper) > 0 else None
            rc = solution.col_dual[i] if col_values and len(solution.col_dual) > i else None

            obj_lower = None
            obj_upper = None
            if rc is not None and abs(rc) > 1e-10:
                if i < len(col_values) and abs(col_values[i]) < 1e-10:
                    if rc > 0:
                        obj_upper = cost + abs(rc)
                    else:
                        obj_lower = cost - abs(rc)

            objective_ranges.append(SensitivityRange(
                name=f"col_{i}",
                current=float(cost),
                lower=float(obj_lower) if obj_lower is not None else None,
                upper=float(obj_upper) if obj_upper is not None else None,
                reduced_cost=float(rc) if rc is not None else None,
            ))

        for i in range(num_rows):
            dual_val = row_dual[i] if i < len(row_dual) else None
            rhs_val = 0.0
            lower = -1e30
            upper = 1e30
            try:
                row_info = hp.getRowsByRange(i, i + 1) if hasattr(hp, 'getRowsByRange') else None
                if row_info:
                    lower = row_info.lower[0] if hasattr(row_info, 'lower') and len(row_info.lower) > 0 else -1e30
                    upper = row_info.upper[0] if hasattr(row_info, 'upper') and len(row_info.upper) > 0 else 1e30
                    if abs(lower - upper) < 1e-10:
                        rhs_val = lower
                    elif abs(lower) > 1e20:
                        rhs_val = upper
                    else:
                        rhs_val = lower
            except Exception:
                pass

            rhs_lower = None
            rhs_upper = None
            if dual_val is not None and abs(dual_val) > 1e-10:
                if dual_val > 0:
                    rhs_lower = rhs_val - 1e10
                    rhs_upper = rhs_val
                else:
                    rhs_lower = rhs_val
                    rhs_upper = rhs_val + 1e10

            rhs_ranges.append(SensitivityRange(
                name=f"row_{i}",
                current=float(rhs_val),
                lower=float(rhs_lower) if rhs_lower is not None else None,
                upper=float(rhs_upper) if rhs_upper is not None else None,
                dual_value=float(dual_val) if dual_val is not None else None,
            ))

        return SensitivityAnalysis(
            objective_ranges=objective_ranges,
            rhs_ranges=rhs_ranges,
        )

    except Exception:
        return None


def extract_glpk_sensitivity(prob: Any, variables_list: list[str],
                             constraints: list[Any]) -> SensitivityAnalysis | None:
    """
    Extrae analisis de sensibilidad de un problema GLPK resuelto.

    GLPK no expone ranging via swiglpk directamente.
    Se estima usando los valores duales y costos reducidos.
    """
    if prob is None:
        return None

    try:
        import swiglpk

        objective_ranges: list[SensitivityRange] = []
        rhs_ranges: list[SensitivityRange] = []

        for i, var in enumerate(variables_list):
            rc = swiglpk.glp_get_col_dual(prob, i + 1)
            cost = swiglpk.glp_get_obj_coef(prob, i + 1)

            obj_lower = None
            obj_upper = None
            if abs(rc) > 1e-10:
                if rc > 0:
                    obj_upper = cost + abs(rc)
                else:
                    obj_lower = cost - abs(rc)

            objective_ranges.append(SensitivityRange(
                name=var,
                current=float(cost),
                lower=float(obj_lower) if obj_lower is not None else None,
                upper=float(obj_upper) if obj_upper is not None else None,
                reduced_cost=float(rc),
            ))

        for i, constr in enumerate(constraints):
            pi = swiglpk.glp_get_row_dual(prob, i + 1)
            rhs = constr.rhs

            rhs_lower = None
            rhs_upper = None
            if abs(pi) > 1e-10:
                if pi > 0:
                    rhs_lower = rhs - 1e10
                    rhs_upper = rhs
                else:
                    rhs_lower = rhs
                    rhs_upper = rhs + 1e10

            rhs_ranges.append(SensitivityRange(
                name=constr.name or f"R{i}",
                current=float(rhs),
                lower=float(rhs_lower) if rhs_lower is not None else None,
                upper=float(rhs_upper) if rhs_upper is not None else None,
                dual_value=float(pi),
            ))

        return SensitivityAnalysis(
            objective_ranges=objective_ranges,
            rhs_ranges=rhs_ranges,
        )

    except Exception:
        return None


def extract_gurobi_sensitivity(model: Any) -> SensitivityAnalysis | None:
    """
    Extrae analisis de sensibilidad de un modelo Gurobi resuelto.

    Gurobi proporciona ranging nativo via SAObjLow, SAObjUp,
    SARHSLow, SARHSUp.
    """
    if model is None:
        return None

    try:
        from gurobipy import GRB

        vars_list = model.getVars()
        constrs_list = model.getConstrs()

        objective_ranges: list[SensitivityRange] = []
        rhs_ranges: list[SensitivityRange] = []

        for v in vars_list:
            try:
                obj_low = v.getAttr(GRB.Attr.SAObjLow)
                obj_up = v.getAttr(GRB.Attr.SAObjUp)
                rc = v.getAttr(GRB.Attr.RC)
            except Exception:
                obj_low = None
                obj_up = None
                rc = None

            objective_ranges.append(SensitivityRange(
                name=v.varName,
                current=float(v.getAttr(GRB.Attr.Obj)),
                lower=float(obj_low) if obj_low is not None else None,
                upper=float(obj_up) if obj_up is not None else None,
                reduced_cost=float(rc) if rc is not None else None,
            ))

        for c in constrs_list:
            try:
                rhs_low = c.getAttr(GRB.Attr.SARHSLow)
                rhs_up = c.getAttr(GRB.Attr.SARHSUp)
                pi = c.getAttr(GRB.Attr.Pi)
            except Exception:
                rhs_low = None
                rhs_up = None
                pi = None

            rhs_ranges.append(SensitivityRange(
                name=c.constrName,
                current=float(c.getAttr(GRB.Attr.RHS)),
                lower=float(rhs_low) if rhs_low is not None else None,
                upper=float(rhs_up) if rhs_up is not None else None,
                dual_value=float(pi) if pi is not None else None,
            ))

        return SensitivityAnalysis(
            objective_ranges=objective_ranges,
            rhs_ranges=rhs_ranges,
        )

    except Exception:
        return None
