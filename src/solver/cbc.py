"""
Solver CBC (COIN-OR) para problemas de programacion lineal.
Implementacion usando PuLP.
"""

from typing import Optional

import pulp
from pulp import LpProblem, LpVariable, LpMinimize, LpMaximize, LpBinary, LpContinuous, LpInteger, LpStatus
from ..core import LinearProblem, Solution
from ..matrix import LPBuilder
from .base import BaseSolver, SolverStats, SolverCapabilities


class CBCSolver(BaseSolver):
    """Solver CBC para problemas de programacion lineal."""
    
    def __init__(self, problem: LinearProblem, config: Optional[BaseSolver.Config] = None):
        super().__init__(problem, config)
        self._solution: Optional[Solution] = None
        self._iterations = 0
        self._nodes = 0
        self._lp = None  # Lazy loading
        
        self.capabilities = SolverCapabilities(
            lp=True,
            milp=True,
            qp=False,
            duals=True,
            warm_start=False,
            sensitivity=False
        )
    
    @property
    def solver_name(self) -> str:
        return "cbc"
    
    @property
    def solver_version(self) -> str:
        try:
            return f"PuLP {pulp.__version__}"
        except Exception:
            return "PuLP"
    
    @property
    def lp(self):
        """Get PolarsLP representation (lazy build)."""
        if self._lp is None:
            self._lp = LPBuilder(self.problem).build()
        return self._lp
    
    def _build_problem(self, problem: LinearProblem) -> 'LpProblem':
        """Construye el problema PuLP."""
        sense = LpMaximize if problem.sense.lower() == "max" else LpMinimize
        prob = LpProblem("LP", sense)
        
        # F3-12: MILP support - variable types
        var_types = problem.variable_types if problem.variable_types else {}
        variables = {}
        for var in problem.variables:
            bound = problem.bounds.get(var)
            
            lb = 0
            ub = None
            
            if bound:
                if bound.lower is not None:
                    lb = bound.lower
                if bound.upper is not None:
                    ub = bound.upper
            
            # Set variable type (F3-12)
            vtype = var_types.get(var, "continuous")
            if vtype == "integer":
                variables[var] = LpVariable(var, lowBound=lb, upBound=ub, cat=LpInteger)
            elif vtype == "binary":
                variables[var] = LpVariable(var, lowBound=lb, upBound=ub, cat=LpBinary)
            else:
                variables[var] = LpVariable(var, lowBound=lb, upBound=ub, cat=LpContinuous)
        
        terms = []
        for var in problem.variables:
            coeff = problem.objective.get(var, 0)
            if coeff != 0:
                terms.append(coeff * variables[var])
        
        if terms:
            prob += sum(terms), "Objetivo"
        
        for i, constraint in enumerate(problem.constraints):
            expr = sum(
                coeff * variables[var]
                for var, coeff in constraint.coefficients.items()
            )
            
            if constraint.sense in ("<=", "<"):
                prob += (expr <= constraint.rhs), f"c{i}"
            elif constraint.sense in (">=", ">"):
                prob += (expr >= constraint.rhs), f"c{i}"
            else:
                prob += (expr == constraint.rhs), f"c{i}"
        
        return prob
    
    def solve(self) -> Solution:
        """Resuelve el problema."""
        if self.problem is None:
            return Solution(
                status="ERROR: No problem set",
                objective_value=None,
                variables={},
            )
        
        try:
            prob = self._build_problem(self.problem)
            
            # F3-12, F3-16: CBC solver options
            solver_options = []
            if self.config.mip_gap is not None:
                solver_options.append(("ratioGap", self.config.mip_gap))
            if self.config.time_limit is not None:
                solver_options.append(("sec", self.config.time_limit))
            if self.config.threads is not None:
                solver_options.append(("threads", self.config.threads))
            
            solver = pulp.PULP_CBC_CMD(msg=self.config.verbose, options=solver_options)
            
            prob.solve(solver)
            
            status_map = {
                "Optimal": "OPTIMAL",
                "Not Solved": "NOT_SOLVED",
                "Infeasible": "INFEASIBLE",
                "Unbounded": "UNBOUNDED",
                "Undefined": "UNDEFINED",
            }
            status = status_map.get(LpStatus[prob.status], str(prob.status))
            
            variables = {}
            dual_values = {}
            reduced_costs = {}
            obj_value = None
            
            if status == "OPTIMAL":
                for var in prob.variables():
                    if var.varValue is not None:
                        variables[var.name] = var.varValue
                obj_val = pulp.value(prob.objective)
                obj_value = float(obj_val) if obj_val is not None else None
                try:
                    self._iterations = getattr(prob.solver, 'iterations', 0) or 0
                except Exception as e:
                    self._iterations = 0
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"No se pudieron extraer iteraciones de CBC: {e}")
                
                # Try to get dual values and reduced costs
                try:
                    for constr in prob.constraints.values():
                        if hasattr(constr, 'pi'):
                            dual_values[constr.name] = constr.pi
                    for var in prob.variables():
                        if hasattr(var, 'dj'):
                            reduced_costs[var.name] = var.dj
                except Exception as e:
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"No se pudieron extraer duales/reduced costs de CBC: {e}")
            
            self._solution = Solution(
                status=status,
                objective_value=obj_value,
                variables=variables,
                dual_values=dual_values if dual_values else None,
                reduced_costs=reduced_costs if reduced_costs else None,
                numerical_quality=self._build_numerical_quality(prob),
            )
            
            return self._solution
            
        except Exception as e:
            return Solution(
                status=f"ERROR: {str(e)}",
                objective_value=None,
                variables={},
            )
    
    def _build_numerical_quality(self, prob) -> object:
        """Construye NumericalQuality con metricas MILP de CBC."""
        try:
            from ..core import NumericalQuality
            nodes = self._nodes
            runtime = max(getattr(self.stats, 'solve_time', 0.001), 0.001)
            return NumericalQuality(
                mip_gap=0.0,
                nodes_per_second=nodes / runtime if nodes > 0 else 0.0,
            )
        except Exception:
            return None
    
    def get_stats(self) -> SolverStats:
        """Obtiene estadisticas de la resolucion."""
        return SolverStats(
            iterations=self._iterations,
            nodes=self._nodes
        )