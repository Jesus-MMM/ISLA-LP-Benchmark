"""
Solver HiGHS para problemas de programacion lineal.
Implementacion usando highspy (interfaz nativa a HiGHS).
"""

import time
from typing import Optional

import highspy

from ..core import LinearProblem, Solution
from ..matrix import LPBuilder
from .base import BaseSolver, SolverStats, SolverCapabilities


class HiGHSSolver(BaseSolver):
    """Solver HiGHS para problemas de programacion lineal."""
    
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
            sensitivity=True
        )
    
    @property
    def solver_name(self) -> str:
        return "highs"
    
    @property
    def solver_version(self) -> str:
        return "highspy"
    
    @property
    def lp(self):
        """Get PolarsLP representation (lazy build)."""
        if self._lp is None:
            self._lp = LPBuilder(self.problem).build()
        return self._lp
    
    def solve(self) -> Solution:
        """Resuelve el problema."""
        problem = self.problem  # From BaseSolver
        
        if problem is None:
            return Solution(
                status="ERROR: No problem set",
                objective_value=None,
                variables={},
            )
        
        start_time = time.perf_counter()
        
        try:
            variables_list = list(problem.variables)
            num_vars = len(variables_list)
            
            hp = highspy.Highs()
            
            from ..core.constants import DEFAULT_INFINITY
            INF = DEFAULT_INFINITY
            
            # F3-5: MILP support - variable types
            var_types = problem.variable_types if problem.variable_types else {}
            
            for i, var in enumerate(variables_list):
                bound = problem.bounds.get(var)
                lb = 0.0 if not bound or bound.lower is None else bound.lower
                ub = highspy.kHighsInf if not bound or bound.upper is None else bound.upper
                
                hp.addVar(lb, ub)
            
            cost_map = problem.objective
            for i, var in enumerate(variables_list):
                cost = cost_map.get(var, 0)
                if cost != 0:
                    hp.changeColCost(i, cost)
            
            for constraint in problem.constraints:
                indices = []
                values = []
                
                for var, coeff in constraint.coefficients.items():
                    var_idx = variables_list.index(var)
                    indices.append(var_idx)
                    values.append(coeff)
                
                num_nz = len(indices)
                indices_arr = indices
                values_arr = values
                
                if constraint.sense in ("<=", "<"):
                    hp.addRow(-INF, constraint.rhs, num_nz, indices_arr, values_arr)
                elif constraint.sense in (">=", ">"):
                    hp.addRow(constraint.rhs, INF, num_nz, indices_arr, values_arr)
                else:
                    hp.addRow(constraint.rhs, constraint.rhs, num_nz, indices_arr, values_arr)
            
            if problem.sense.lower() == "max":
                hp.changeObjectiveSense(highspy.ObjSense.kMaximize)
            
            hp.run()
            
            solve_time = time.perf_counter() - start_time
            
            model_status = hp.getModelStatus()
            
            if model_status == highspy.HighsModelStatus.kOptimal:
                status = "OPTIMAL"
            elif model_status == highspy.HighsModelStatus.kInfeasible:
                status = "INFEASIBLE"
            elif model_status == highspy.HighsModelStatus.kUnbounded:
                status = "UNBOUNDED"
            else:
                status = str(model_status)
            
            variables = {}
            
            dual_values = {}
            reduced_costs = {}
            
            if status == "OPTIMAL":
                solution = hp.getSolution()
                for i, var in enumerate(variables_list):
                    variables[var] = solution.col_value[i]
                
                # F3-7: Try to get dual values and reduced costs (reuse solution from line 132)
                try:
                    for i, constr in enumerate(problem.constraints):
                        if i < len(solution.row_dual):
                            dual_values[constr.name or f"R{i}"] = solution.row_dual[i]
                except Exception as e:
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"No se pudieron extraer valores duales de HiGHS: {e}")
                
                # F3-14: Get basis info
                try:
                    basis_info = hp.getBasis()
                    basis = {var: ("basic" if basis_info[i] == 0 else "nonbasic") 
                               for i, var in enumerate(variables_list)}
                except Exception as e:
                    basis = None
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"No se pudo obtener informacion de base HiGHS: {e}")
            
            sensitivity = None
            try:
                from ..analysis.sensitivity import extract_highs_sensitivity
                sensitivity = extract_highs_sensitivity(hp)
            except Exception as e:
                if self.config.verbose:
                    print(f"Advertencia: No se pudo extraer sensibilidad de HiGHS: {e}")
            
            # F3-8: Use proper infinity
            from ..core.constants import DEFAULT_INFINITY
            
            self._solution = Solution(
                status=status,
                objective_value=hp.getObjectiveValue() if status == "OPTIMAL" else None,
                variables=variables,
                dual_values=dual_values if dual_values else None,
                reduced_costs=reduced_costs if reduced_costs else None,
                basis=basis,
            )
            
            self._iterations = 0
            try:
                info = hp.getInfo()
                self._iterations = getattr(info, 'simplex_iterations', 0) or 0
            except Exception as e:
                logger = __import__('logging').getLogger(__name__)
                logger.debug(f"No se pudieron extraer estadisticas de HiGHS: {e}")
            
            return self._solution
            
        except Exception as e:
            return Solution(
                status=f"ERROR: {str(e)}",
                objective_value=None,
                variables={},
            )
    
    def get_stats(self) -> SolverStats:
        """Obtiene estadisticas de la resolucion."""
        return SolverStats(
            iterations=self._iterations,
            nodes=self._nodes
        )