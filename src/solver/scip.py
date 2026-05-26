"""
SCIP Solver for linear and mixed-integer programming.
Implements using PySCIPOpt (interface to SCIP).
"""

from typing import Optional

import pyscipopt as scip

from ..core import LinearProblem, Solution
from .base import BaseSolver, SolverStats, SolverCapabilities

class SCIPSolver(BaseSolver):
    """SCIP Solver for linear and mixed-integer programming."""
    
    def __init__(self, problem: LinearProblem, config: Optional[BaseSolver.Config] = None):
        super().__init__(problem, config)
        self._solution: Optional[Solution] = None
        self._iterations = 0
        self._nodes = 0
        
        self.capabilities = SolverCapabilities(
            lp=True,
            milp=True,
            qp=False,
            duals=True,
            warm_start=True,
            sensitivity=False
        )
    
    @property
    def solver_name(self) -> str:
        return "scip"
    
    @property
    def solver_version(self) -> str:
        try:
            return scip.__version__
        except Exception:
            return "SCIP"
    
    @property
    def is_available(self) -> bool:
        return True
    
    def solve(self) -> Solution:
        """Solves the problem."""
        problem = self.problem
        
        if problem is None:
            return Solution(
                status="ERROR: No problem set",
                objective_value=None,
                variables={},
            )
        
        try:
            model = scip.Model("LP")
            
            if not self.config.verbose:
                model.hideOutput()
            
            # F4-2: MILP support - variable types
            variables = {}
            var_types = problem.variable_types if problem.variable_types else {}
            
            for var in problem.variables:
                bound = problem.bounds.get(var)
                lb = 0.0 if not bound or bound.lower is None else bound.lower
                ub = None if not bound or bound.upper is None else bound.upper
                
                vtype = var_types.get(var, "continuous")
                if vtype == "integer":
                    scip_var = model.addVar(var, lb=lb, ub=ub, vtype="INTEGER")
                elif vtype == "binary":
                    scip_var = model.addVar(var, lb=0.0, ub=1.0, vtype="BINARY")
                else:
                    scip_var = model.addVar(var, lb=lb, ub=ub, vtype="CONTINUOUS")
                
                variables[var] = scip_var
            
            # Set objective
            obj_expr = sum(
                coeff * variables[var]
                for var, coeff in problem.objective.items()
                if coeff != 0
            )
            model.setObjective(obj_expr)
            
            # Set sense
            if problem.sense.lower() == "max":
                model.setMaximize()
            else:
                model.setMinimize()
            
            # Add constraints
            for i, constraint in enumerate(problem.constraints):
                expr = sum(
                    coeff * variables[var]
                    for var, coeff in constraint.coefficients.items()
                )
                
                if constraint.sense == "<=":
                    model.addCons(expr <= constraint.rhs, name=constraint.name or f"R{i}")
                elif constraint.sense == ">=":
                    model.addCons(expr >= constraint.rhs, name=constraint.name or f"R{i}")
                else:
                    model.addCons(expr == constraint.rhs, name=constraint.name or f"R{i}")
            
            # F4-2: Configure solver
            if self.config.time_limit is not None:
                model.setRealParam("limits/time", self.config.time_limit)
            if self.config.mip_gap is not None:
                model.setRealParam("limits/gap", self.config.mip_gap)
            if self.config.threads is not None:
                model.setIntParam("parallel/maxnthreads", self.config.threads)
            
            model.optimize()
            
            status_map = {
                "optimal": "OPTIMAL",
                "infeasible": "INFEASIBLE",
                "unbounded": "UNBOUNDED",
                "inforunb": "INFEASIBLE_OR_UNBOUNDED",
                "timelimit": "TIME_LIMIT",
                "nodelimit": "NODE_LIMIT",
                "sollimit": "SOL_LIMIT",
                "unknown": "UNKNOWN",
            }
            
            scip_status = model.getStatus().lower()
            status = status_map.get(scip_status, scip_status.upper())
            
            sol_vars = {}
            obj_value = None
            
            if status == "OPTIMAL":
                for var_name, var_obj in variables.items():
                    sol_vars[var_name] = model.getVal(var_obj)
                
                obj_value = model.getObjVal()
                
                # F4-2: Get dual values and reduced costs
                dual_values = {}
                reduced_costs = {}
                
                try:
                    # Get SCIP constraints
                    scip_cons = model.getConss()
                    for i, cons in enumerate(scip_cons):
                        dual = model.getDualsolLinear(cons)
                        if abs(dual) > 1e-10:
                            dual_values[problem.constraints[i].name or f"R{i}"] = dual
                    
                    for var_name, var_obj in variables.items():
                        rc = model.getRedcostVar(var_obj)
                        if abs(rc) > 1e-10:
                            reduced_costs[var_name] = rc
                except Exception as e:
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"No se pudieron extraer duales/reduced costs de SCIP: {e}")
                
                self._solution = Solution(
                    status=status,
                    objective_value=obj_value,
                    variables=sol_vars,
                    dual_values=dual_values if dual_values else None,
                    reduced_costs=reduced_costs if reduced_costs else None,
                    iterations=self._iterations,
                    nodes=self._nodes,
                )
            else:
                self._solution = Solution(
                    status=status,
                    objective_value=None,
                    variables={},
                )
            
            return self._solution
            
        except Exception as e:
            return Solution(
                status=f"ERROR: {str(e)}",
                objective_value=None,
                variables={},
            )
    
    def get_stats(self) -> SolverStats:
        """Gets solution statistics."""
        return SolverStats(
            iterations=self._iterations,
            nodes=self._nodes,
        )
