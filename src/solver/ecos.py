"""
Solver ECOS para problemas de programacion lineal.
Implementacion usando ecos (Embedded Conic Solver).
"""

try:
    import ecos
    _is_solver_available = True
except ImportError:
    _is_solver_available = False

from typing import Optional

from ..core import LinearProblem, Solution
from .base import BaseSolver, SolverStats, SolverCapabilities


class ECOSSolver(BaseSolver):
    """Solver ECOS para problemas de programacion lineal.
    """

    def __init__(self, problem: LinearProblem, config: Optional[BaseSolver.Config] = None):
        super().__init__(problem, config)
        self.capabilities = SolverCapabilities(
            lp=True,
            milp=False,
            qp=False,
            duals=True,
            warm_start=False,
            sensitivity=False
        )

    @property
    def solver_name(self) -> str:
        return "ecos"

    @property
    def solver_version(self) -> str:
        if _is_solver_available:
            try:
                return ecos.__version__
            except Exception:
                return "ecos"
        return "ecos (not installed)"

    @property
    def is_available(self) -> bool:
        return _is_solver_available

    def solve(self) -> Solution:
        """Resuelve el problema usando ECOS.

        Returns:
            Solution: Objeto con la solucion del problema.
        """
        problem = self.problem

        if problem is None:
            return Solution(
                status="ERROR: No problem set",
                objective_value=None,
                variables={},
            )

        try:
            import numpy as np
            import ecos
            from scipy import sparse
        except ImportError as e:
            return Solution(
                status=f"ERROR: ecos or scipy not available: {e}",
                objective_value=None,
                variables={},
            )

        try:
            if problem.is_mip:
                return Solution(
                    status="ERROR: ECOS does not support MIP",
                    objective_value=None,
                    variables={},
                )

            variables_list = list(problem.variables)
            n = len(variables_list)

            c = np.array(
                [problem.objective.get(v, 0.0) for v in variables_list],
                dtype=float,
            )
            if problem.sense.lower() == "max":
                c = -c

            G_rows = []
            h_vals = []
            constraint_order = []

            for constr in problem.constraints:
                name = constr.name or f"R{problem.constraints.index(constr)}"
                if constr.sense == "=":
                    continue
                coeffs = [constr.coefficients.get(v, 0.0) for v in variables_list]
                if constr.sense in (">=", ">"):
                    G_rows.append([-x for x in coeffs])
                    h_vals.append(-constr.rhs)
                else:
                    G_rows.append(coeffs)
                    h_vals.append(constr.rhs)
                constraint_order.append(name)

            for var in variables_list:
                bound = problem.bounds.get(var)
                if bound:
                    idx = variables_list.index(var)
                    if bound.lower is not None:
                        row = [0.0] * n
                        row[idx] = -1.0
                        G_rows.append(row)
                        h_vals.append(-bound.lower)
                    if bound.upper is not None:
                        row = [0.0] * n
                        row[idx] = 1.0
                        G_rows.append(row)
                        h_vals.append(bound.upper)

            equality_rows = []
            equality_rhs = []
            for constr in problem.constraints:
                if constr.sense == "=":
                    equality_rows.append(
                        [constr.coefficients.get(v, 0.0) for v in variables_list]
                    )
                    equality_rhs.append(constr.rhs)

            if G_rows:
                G = sparse.csc_matrix(G_rows, dtype=float)
                h = np.array(h_vals, dtype=float)
                dims = {"l": G.shape[0], "q": [], "s": []}
            else:
                G = None
                h = None
                dims = {"l": 0, "q": [], "s": []}
            if equality_rows:
                A = sparse.csc_matrix(equality_rows, dtype=float)
                b = np.array(equality_rhs, dtype=float)
            else:
                A = None
                b = None


            sol = ecos.solve(
                c, G, h, dims, A, b,
                verbose=self.config.verbose,
            )

            variables = {}
            dual_values = None
            objective_value = None
            self._iterations = 0

            if sol is None:
                status = "ERROR: solver returned None"
            elif "x" not in sol:
                status = "ERROR: solver result incomplete"
            else:
                x = sol["x"]
                for i, var in enumerate(variables_list):
                    variables[var] = float(x[i])

                info = sol.get("info", {}) if isinstance(sol, dict) else {}
                pcost = info.get("pcost") if isinstance(info, dict) else None
                if pcost is not None:
                    objective_value = float(pcost)
                else:
                    objective_value = float(np.dot(c, x))
                if problem.sense.lower() == "max":
                    objective_value = -objective_value

                info_exitflag = info.get("exitflag", 0) if isinstance(info, dict) else 0
                if info_exitflag == 0:
                    status = "OPTIMAL"
                elif info_exitflag == 1:
                    status = "INFEASIBLE"
                elif info_exitflag == 2:
                    status = "UNBOUNDED"
                else:
                    status = "OPTIMAL"

                y = sol.get("y")
                if y is not None and constraint_order:
                    dual_values = {}
                    for i, name in enumerate(constraint_order):
                        if i < len(y):
                            dual_values[name] = float(y[i])

                self._iterations = int(info.get("iter", 0) if isinstance(info, dict) else 0)

            return Solution(
                status=status,
                objective_value=objective_value,
                variables=variables,
                dual_values=dual_values,
                reduced_costs=None,
                iterations=self._iterations,
            )

        except Exception as e:
            return Solution(
                status=f"ERROR: {str(e)}",
                objective_value=None,
                variables={},
            )

    def get_stats(self) -> SolverStats:
        """Obtiene estadisticas de la ultima ejecucion."""
        return SolverStats(
            iterations=self._iterations,
            nodes=0,
        )
