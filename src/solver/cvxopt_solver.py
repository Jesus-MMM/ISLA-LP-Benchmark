"""
Solver CVXOPT para problemas de programacion lineal.
Implementacion usando cvxopt (solvers.lp).
"""

try:
    import cvxopt
    _is_solver_available = True
except ImportError:
    _is_solver_available = False

from typing import Optional

from ..core import LinearProblem, Solution
from ..matrix import MatrixConverter
from .base import BaseSolver, SolverStats, SolverCapabilities


class CVXOPTSolver(BaseSolver):
    """Solver CVXOPT para problemas de programacion lineal.
    """

    def __init__(self, problem: LinearProblem, config: Optional[BaseSolver.Config] = None):
        super().__init__(problem, config)
        self.capabilities = SolverCapabilities(
            lp=True,
            milp=False,
            qp=True,
            duals=True,
            warm_start=False,
            sensitivity=False
        )

    @property
    def solver_name(self) -> str:
        return "cvxopt"

    @property
    def solver_version(self) -> str:
        if _is_solver_available:
            try:
                return cvxopt.__version__
            except Exception:
                return "cvxopt"
        return "cvxopt (not installed)"

    @property
    def is_available(self) -> bool:
        return _is_solver_available

    def solve(self) -> Solution:
        """Resuelve el problema usando CVXOPT.

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
            from cvxopt import matrix, solvers as cvx_solvers
        except ImportError as e:
            return Solution(
                status=f"ERROR: cvxopt not available: {e}",
                objective_value=None,
                variables={},
            )

        try:
            if problem.is_mip:
                return Solution(
                    status="ERROR: CVXOPT does not support MIP",
                    objective_value=None,
                    variables={},
                )

            data = MatrixConverter.to_cvxopt(problem)
            variables_list = list(problem.variables)

            cvx_solvers.options["show_progress"] = self.config.verbose

            c_m = matrix(data["c"])

            if data["G"] is not None:
                G_m = matrix(data["G"])
                h_m = matrix(data["h"])
            else:
                G_m = None
                h_m = None

            if data["A"] is not None:
                A_m = matrix(data["A"])
                b_m = matrix(data["b"])
            else:
                A_m = None
                b_m = None

            sol = cvx_solvers.lp(c_m, G_m, h_m, A_m, b_m)

            cvx_status = sol["status"]
            if cvx_status == "optimal":
                status = "OPTIMAL"
            elif cvx_status == "primal infeasible":
                status = "INFEASIBLE"
            elif cvx_status == "dual infeasible":
                status = "UNBOUNDED"
            else:
                status = f"ERROR: {cvx_status}"

            variables = {}
            dual_values = None
            objective_value = None

            if status == "OPTIMAL":
                x = sol["x"]
                for i, var in enumerate(variables_list):
                    variables[var] = float(x[i])

                objective_value = float(sol["primal objective"])
                if problem.sense.lower() == "max":
                    objective_value = -objective_value

                z = sol.get("z")
                constraint_order = data["constraint_order"]
                if z is not None and len(z) > 0 and constraint_order:
                    dual_values = {}
                    for i, name in enumerate(constraint_order):
                        if i < len(z):
                            dual_values[name] = float(z[i])

            return Solution(
                status=status,
                objective_value=objective_value,
                variables=variables,
                dual_values=dual_values,
                reduced_costs=None,
                iterations=int(sol.get("iterations", 0)),
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
            iterations=0,
            nodes=0,
        )
