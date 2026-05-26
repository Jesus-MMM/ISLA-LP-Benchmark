"""
Solver Ipopt para problemas de programacion lineal.
Implementacion usando CasADi (interfaz Python a Ipopt).
"""

try:
    import casadi as ca
    _is_solver_available = True
except ImportError:
    _is_solver_available = False

from typing import Optional

from ..core import LinearProblem, Solution
from .base import BaseSolver, SolverStats, SolverCapabilities


class IpoptSolver(BaseSolver):
    """Solver Ipopt para problemas de programacion lineal usando CasADi."""

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
        return "ipopt"

    @property
    def solver_version(self) -> str:
        if _is_solver_available:
            try:
                return ca.__version__
            except Exception:
                return "casadi"
        return "casadi (not installed)"

    @property
    def is_available(self) -> bool:
        return _is_solver_available

    def solve(self) -> Solution:
        problem = self.problem

        if problem is None:
            return Solution(
                status="ERROR: No problem set",
                objective_value=None,
                variables={},
            )

        if problem.is_mip:
            return Solution(
                status="ERROR: Ipopt does not support MIP",
                objective_value=None,
                variables={},
            )

        try:
            variables_list = list(problem.variables)
            n = len(variables_list)

            opti = ca.Opti()
            x = opti.variable(n)

            obj_expr = 0
            for var in variables_list:
                coeff = problem.objective.get(var, 0.0)
                idx = variables_list.index(var)
                obj_expr += coeff * x[idx]

            if problem.sense.lower() == "max":
                opti.minimize(-obj_expr)
            else:
                opti.minimize(obj_expr)

            bound_count = 0
            for var in variables_list:
                bound = problem.bounds.get(var)
                idx = variables_list.index(var)
                if bound:
                    if bound.lower is not None:
                        opti.subject_to(x[idx] >= bound.lower)
                        bound_count += 1
                    if bound.upper is not None:
                        opti.subject_to(x[idx] <= bound.upper)
                        bound_count += 1
                else:
                    opti.subject_to(x[idx] >= 0)
                    bound_count += 1

            for constr in problem.constraints:
                expr = 0
                for var, coeff in constr.coefficients.items():
                    idx = variables_list.index(var)
                    expr += coeff * x[idx]
                if constr.sense in ("<=", "<"):
                    opti.subject_to(expr <= constr.rhs)
                elif constr.sense in (">=", ">"):
                    opti.subject_to(expr >= constr.rhs)
                else:
                    opti.subject_to(expr == constr.rhs)

            opts = {}
            if not self.config.verbose:
                opts["ipopt.print_level"] = 0
                opts["print_time"] = 0
            else:
                opts["ipopt.print_level"] = 5
            if self.config.time_limit is not None and self.config.time_limit > 0:
                opts["ipopt.max_cpu_time"] = self.config.time_limit

            opti.solver("ipopt", opts)

            sol = opti.solve()

            variables = {}
            for i, var in enumerate(variables_list):
                variables[var] = float(sol.value(x[i]))

            obj_val = float(sol.value(obj_expr))

            dual_values = None
            try:
                lam_g = sol.value(opti.lam_g)
                if lam_g is not None and len(lam_g) >= bound_count + len(problem.constraints):
                    dual_values = {}
                    for i, constr in enumerate(problem.constraints):
                        name = constr.name or f"R{i}"
                        idx = bound_count + i
                        dual_values[name] = float(lam_g[idx])
            except Exception:
                pass

            return Solution(
                status="OPTIMAL",
                objective_value=obj_val,
                variables=variables,
                dual_values=dual_values,
                reduced_costs=None,
            )

        except Exception as e:
            err_str = str(e)
            status = "ERROR"
            if "Infeasible" in err_str or "infeasible" in err_str:
                status = "INFEASIBLE"
            elif "Unbounded" in err_str or "unbounded" in err_str:
                status = "UNBOUNDED"
            elif "TimeLimit" in err_str or "max_cpu_time" in err_str:
                status = "TIME_LIMIT"
            elif "User_Requested_Stop" in err_str:
                status = "TIME_LIMIT"
            return Solution(
                status=status,
                objective_value=None,
                variables={},
            )

    def get_stats(self) -> SolverStats:
        return SolverStats(
            iterations=0,
            nodes=0,
        )
