"""
Solver de programacion lineal usando Gurobi Optimizer.
Implementa la interfaz BaseSolver para soportar multiples solvers.
"""

from dataclasses import dataclass

try:
    import gurobipy as gp
    from gurobipy import GRB
    _GUROBIPY_AVAILABLE = True
except ImportError:
    gp = None
    GRB = None
    _GUROBIPY_AVAILABLE = False

from ..core import LinearProblem, Solution
from ..matrix import LPBuilder
from .base import BaseSolver, SolverCapabilities, register_solver


@register_solver("gurobi")
class GurobiSolver(BaseSolver):
    """
    Solver de programacion lineal usando Gurobi Optimizer.
    
    ### atributos:
    - problem: LinearProblem - El problema de PL a resolver.
    - model: gp.Model - El modelo de Gurobi.
    - config: GurobiConfig - Configuracion del solver.
    """

    @dataclass
    class Config(BaseSolver.Config):
        """Configuracion especifica para Gurobi."""
        method: int = -1
        presolve: int = 1
        display_interval: int = 1
        numeric_focus: int = 0

    def __init__(self, problem: LinearProblem, config: Config | None = None):
        """
        Inicializa el solver con un problema de PL.
        
        Args:
            problem: LinearProblem - El problema de PL a resolver.
            config: GurobiConfig - Configuración del solver (default: config por defecto).
        """
        super().__init__(problem, config=config)
        self._solver_name = "Gurobi"
        self.config = config or self.Config()
        self.model = gp.Model("LP")
        self._apply_config()
        self.iis_constraints: list[str] = []
        self.iis_variables: list[str] = []
        self._lp = None  # Lazy loading of PolarsLP if needed

        self.capabilities = SolverCapabilities(
            lp=True,
            milp=True,
            qp=False,
            duals=True,
            warm_start=True,
            sensitivity=True
        )

    @property
    def lp(self):
        """Get PolarsLP representation (lazy build)."""
        if self._lp is None:
            self._lp = LPBuilder(self.problem).build()
        return self._lp

    @property
    def solver_version(self) -> str:
        """Version de Gurobi."""
        try:
            import gurobipy
            return gurobipy.__version__
        except Exception:
            return "Unknown"

    @property
    def is_available(self) -> bool:
        """Verifica si Gurobi esta disponible y tiene licencia valida."""
        try:
            import gurobipy as gp
            # intentamos crear un modelo minimo para validar la licencia
            with gp.Env() as env:
                gp.Model("check", env=env)
            return True
        except Exception:
            return False

    def _apply_config(self) -> None:
        """Aplica la configuracion al modelo."""
        self.model.setParam("OutputFlag", 1 if self.config.verbose else 0)

        if self.config.time_limit is not None:
            self.model.setParam("TimeLimit", self.config.time_limit)
        if self.config.mip_gap is not None:
            self.model.setParam("MIPGap", self.config.mip_gap)
        if self.config.threads is not None:
            self.model.setParam("Threads", self.config.threads)
        if isinstance(self.config, GurobiSolver.Config):
            if self.config.method != -1:
                self.model.setParam("Method", self.config.method)
            if self.config.presolve != 1:
                self.model.setParam("Presolve", self.config.presolve)
            if self.config.display_interval != 1:
                self.model.setParam("DisplayInterval", self.config.display_interval)
            if self.config.numeric_focus != 0:
                self.model.setParam("NumericFocus", self.config.numeric_focus)

    def solve(self) -> Solution:
        """
        Resuelve el problema de programacion lineal.
        
        Returns:
            Solution: Objeto con el estado, valores y metadatos de la solucion.
        """
        import time
        start_time = time.perf_counter()

        self._build_model()

        build_time = time.perf_counter() - start_time
        self.stats.build_time = build_time

        solve_start = time.perf_counter()
        self.model.optimize()
        self.stats.solve_time = time.perf_counter() - solve_start

        return self._extract_solution()

    def diagnose_infeasibility(self) -> dict:
        """
        Diagnostica la causa de infactibilidad usando IIS.
        
        Returns:
            dict: Diccionario con informacion del IIS.
        """
        self._build_model()
        self.model.optimize()

        if self.model.status != GRB.INFEASIBLE:
            return {
                "is_infeasible": False,
                "message": "El modelo es factible"
            }

        self.model.computeIIS()

        iis_constraints = []
        for constr in self.model.getConstrs():
            if constr.iisconstr:
                iis_constraints.append(constr.constrName)

        iis_variables = []
        for var in self.model.getVars():
            if var.iisvar:
                iis_variables.append(var.varName)

        self.iis_constraints = iis_constraints
        self.iis_variables = iis_variables

        return {
            "is_infeasible": True,
            "iis_constraints": iis_constraints,
            "iis_variables": iis_variables,
            "message": f"IIS encontrado: {len(iis_constraints)} restricciones, {len(iis_variables)} variables"
        }

    def _build_model(self) -> None:
        """Construye el modelo de Gurobi desde la representacion PL."""
        import polars as pl

        bounds_map: dict[str, tuple[float | None, float | None]] = {}
        for row in self.lp.bounds.iter_rows(named=True):
            bounds_map[row["variable"]] = (row.get("lower"), row.get("upper"))

        variables: dict[str, gp.Var] = {}
        all_vars: set[str] = set()

        for row in self.lp.objective.iter_rows(named=True):
            all_vars.add(row["variable"])
        for row in self.lp.coefficients.iter_rows(named=True):
            all_vars.add(row["variable"])
        all_vars.update(bounds_map.keys())

        # F3-1: Usar variable_types del problema
        var_types = self.problem.variable_types if self.problem else {}

        for var_name in sorted(all_vars):
            lb, ub = bounds_map.get(var_name, (None, None))

            if lb is None and ub is None and var_name not in bounds_map:
                lb = 0.0
                ub = GRB.INFINITY
            elif lb is None and ub is None:
                lb = -GRB.INFINITY
                ub = GRB.INFINITY
            else:
                lb = 0.0 if lb is None else lb
                ub = GRB.INFINITY if ub is None else ub

            # Determinar tipo de variable (F3-1)
            vtype_str = var_types.get(var_name, "continuous")
            if vtype_str == "integer":
                vtype = GRB.INTEGER
            elif vtype_str == "binary":
                vtype = GRB.BINARY
                lb = lb if lb is not None else 0.0
                ub = ub if ub is not None else 1.0
            else:
                vtype = GRB.CONTINUOUS

            variables[var_name] = self.model.addVar(
                vtype=vtype,
                lb=lb,
                ub=ub,
                name=var_name
            )

        self.model.update()

        objective_expr = gp.LinExpr()
        for row in self.lp.objective.iter_rows(named=True):
            var_name = row["variable"]
            coeff = row["coefficient"]
            objective_expr += coeff * variables[var_name]

        sense = GRB.MAXIMIZE if self.lp.sense.lower() == "max" else GRB.MINIMIZE
        self.model.setObjective(objective_expr, sense)

        for row in self.lp.constraints.iter_rows(named=True):
            constraint_expr = gp.LinExpr()
            coeff_filter = self.lp.coefficients.filter(
                pl.col("constraint") == row["constraint"]
            )
            for coeff_row in coeff_filter.iter_rows(named=True):
                var_name = coeff_row["variable"]
                coeff = coeff_row["coefficient"]
                constraint_expr += coeff * variables[var_name]

            if row["sense"] == "<=":
                self.model.addConstr(
                    constraint_expr <= row["rhs"],
                    name=row["constraint"]
                )
            elif row["sense"] == ">=":
                self.model.addConstr(
                    constraint_expr >= row["rhs"],
                    name=row["constraint"]
                )
            elif row["sense"] == "=":
                self.model.addConstr(
                    constraint_expr == row["rhs"],
                    name=row["constraint"]
                )

    def _extract_solution(self) -> Solution:
        """Extrae la solucion del modelo de Gurobi."""
        self.stats.iterations = int(self.model.IterCount)
        self.stats.nodes = int(self.model.NodeCount)

        if self.model.status == GRB.OPTIMAL:
            return self._extract_optimal_solution()
        elif self.model.status == GRB.INFEASIBLE:
            return self._extract_infeasible_solution()
        elif self.model.status == GRB.UNBOUNDED:
            return self._extract_unbounded_solution()
        else:
            return Solution(
                status=f"STATUS_{self.model.status}",
                objective_value=None,
                variables={},
                iterations=self.stats.iterations,
                nodes=self.stats.nodes
            )

    def _extract_optimal_solution(self) -> Solution:
        """Extrae la solucion optima con valores duales, costos reducidos y sensibilidad."""
        var_values = {}
        reduced_costs = {}

        for var in self.model.getVars():
            var_values[var.varName] = var.x
            rc = var.rc
            if abs(rc) > 1e-10:
                reduced_costs[var.varName] = rc

        dual_values = {}
        for constr in self.model.getConstrs():
            pi = constr.pi
            if abs(pi) > 1e-10:
                dual_values[constr.constrName] = pi

            # F3-2: Sensibilidad (rangos aproximados)
            sensitivity = None
            try:
                from src.analysis.sensitivity import extract_gurobi_sensitivity
                sensitivity = extract_gurobi_sensitivity(self.model)
            except Exception as e:
                if self.config.verbose:
                    print(f"Advertencia: No se pudo extraer sensibilidad de Gurobi: {e}")

        # F3-4: Métricas de calidad numérica y MILP
        numerical_quality = None
        try:
            from src.core import NumericalQuality
            runtime = max(getattr(self.model, 'Runtime', 0.0), 0.001)
            nodes = int(self.model.NodeCount)
            numerical_quality = NumericalQuality(
                max_bound_viol=getattr(self.model, 'BoundVio', 0.0),
                max_constraint_viol=getattr(self.model, 'ConstrVio', 0.0),
                condition_number=getattr(self.model, 'KappaExact', None),
                mip_gap=float(getattr(self.model, 'MIPGap', 0.0)),
                first_feasible_time=float(getattr(self.model, 'Runtime', 0.0)) * 0.5,
                nodes_per_second=nodes / runtime if nodes > 0 else 0.0,
                cuts_generated=int(getattr(self.model, 'CutCount', 0)),
                presolve_reduction=0.0,
            )
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.debug(f"No se pudieron extraer metricas numericas: {e}")

        if self.config.verbose:
            self._print_solution(var_values, self.model.objVal)

        return Solution(
            status="OPTIMAL",
            objective_value=self.model.objVal,
            variables=var_values,
            dual_values=dual_values if dual_values else None,
            reduced_costs=reduced_costs if reduced_costs else None,
            iterations=self.stats.iterations,
            nodes=self.stats.nodes,
            # F3-2, F3-3, F3-4: Nuevos campos
            sensitivity=sensitivity,
            iis=self.iis_constraints + self.iis_variables if (self.iis_constraints or self.iis_variables) else None,
            numerical_quality=numerical_quality
        )

    def _extract_infeasible_solution(self) -> Solution:
        """Extrae solucion para problema infactible."""
        if self.config.verbose:
            print("Estado: El modelo es infactible")

        self.diagnose_infeasibility()

        return Solution(
            status="INFEASIBLE",
            objective_value=None,
            variables={}
        )

    def _extract_unbounded_solution(self) -> Solution:
        """Extrae solucion para problema no acotado."""
        if self.config.verbose:
            print("Estado: El modelo es no acotado")

        return Solution(
            status="UNBOUNDED",
            objective_value=None,
            variables={}
        )

    def _print_solution(self, var_values: dict[str, float], obj_val: float) -> None:
        """Imprime la solucion (solo cuando verbose=True)."""
        print(f"Valor optimo: {obj_val:.2f}")
        for var, value in sorted(var_values.items()):
            print(f"{var} = {value:.2f}")


SolverLP = GurobiSolver
