"""
Solver SCS para problemas de programacion lineal.
Implementacion usando scs (Splitting Conic Solver).
"""

try:
    import scs
    _is_solver_available = True
except ImportError:
    _is_solver_available = False

from typing import Optional

from ..core import LinearProblem, Solution
from .base import BaseSolver, SolverStats, SolverCapabilities


class SCSSolver(BaseSolver):
    """Solver SCS para problemas de programacion lineal.
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
        return "scs"

    @property
    def solver_version(self) -> str:
        if _is_solver_available:
            try:
                return scs.__version__
            except Exception:
                return "scs"
        return "scs (not installed)"

    @property
    def is_available(self) -> bool:
        return _is_solver_available

    def solve(self) -> Solution:
        """Resuelve el problema usando SCS.

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
            from scipy import sparse
            import scs
        except ImportError as e:
            return Solution(
                status=f"ERROR: scs not available: {e}",
                objective_value=None,
                variables={},
            )

        try:
            if problem.is_mip:
                return Solution(
                    status="ERROR: SCS does not support MIP",
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
            A_eq_rows = []
            b_eq_vals = []
            constraint_order = []

            for constr in problem.constraints:
                name = constr.name or f"R{problem.constraints.index(constr)}"
                coeffs = [constr.coefficients.get(v, 0.0) for v in variables_list]
                if constr.sense == "=":
                    A_eq_rows.append(coeffs)
                    b_eq_vals.append(constr.rhs)
                elif constr.sense in (">=", ">"):
                    G_rows.append([-x for x in coeffs])
                    h_vals.append(-constr.rhs)
                    constraint_order.append(name)
                else:
                    G_rows.append(coeffs)
                    h_vals.append(constr.rhs)
                    constraint_order.append(name)

            for var in variables_list:
                bound = problem.bounds.get(var)
                if bound:
                    idx = variables_list.index(var)
                    if bound.lower is not None:
                        G_rows.append([0.0] * idx + [-1.0] + [0.0] * (n - idx - 1))
                        h_vals.append(-bound.lower)
                    if bound.upper is not None:
                        G_rows.append([0.0] * idx + [1.0] + [0.0] * (n - idx - 1))
                        h_vals.append(bound.upper)

            A_parts = []
            if G_rows:
                A_parts.append(np.array(G_rows, dtype=float))
            if A_eq_rows:
                A_parts.append(np.array(A_eq_rows, dtype=float))

            if not A_parts:
                return Solution(
                    status="ERROR: No constraints defined",
                    objective_value=None,
                    variables={},
                )

            A = sparse.csc_matrix(np.vstack(A_parts))
            b = np.concatenate(
                [np.array(h_vals, dtype=float)] +
                ([np.array(b_eq_vals, dtype=float)] if b_eq_vals else [])
            )

            cone = {"l": len(h_vals)}
            if A_eq_rows:
                cone["z"] = len(b_eq_vals)

            data = {"A": A, "b": b, "c": c}
            sol = scs.solve(
                data, cone,
                verbose=self.config.verbose,
            )

            scs_status = sol["info"]["status"]
            if scs_status == "solved":
                status = "OPTIMAL"
            elif scs_status in ("solved inaccurate", "solved/ inaccurate"):
                status = "OPTIMAL (INACCURATE)"
            elif scs_status in ("unbounded", "dual infeasible"):
                status = "UNBOUNDED"
            elif scs_status in ("infeasible", "primal infeasible"):
                status = "INFEASIBLE"
            else:
                status = f"ERROR: {scs_status}"

            variables = {}
            dual_values = None
            objective_value = None

            if status.startswith("OPTIMAL"):
                x = sol["x"]
                for i, var in enumerate(variables_list):
                    variables[var] = float(x[i])

                objective_value = float(sol["info"]["pobj"])
                if problem.sense.lower() == "max":
                    objective_value = -objective_value

                y = sol.get("y")
                if y is not None and constraint_order:
                    dual_values = {}
                    for i, name in enumerate(constraint_order):
                        if i < len(y):
                            dual_values[name] = float(-y[i])

            return Solution(
                status=status,
                objective_value=objective_value,
                variables=variables,
                dual_values=dual_values,
                reduced_costs=None,
                iterations=int(sol["info"].get("iter", 0)),
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
