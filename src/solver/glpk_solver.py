"""
Solver GLPK for linear programming problems.
Implements using swiglpk (native interface to GLPK).
"""

from typing import Optional

import swiglpk

from ..core import LinearProblem, Solution
from ..matrix import LPBuilder, MatrixConverter
from .base import BaseSolver, SolverStats, SolverCapabilities


class GLPKSolver(BaseSolver):
    """GLPK Solver for linear programming problems."""
    
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
        return "glpk"
    
    @property
    def solver_version(self) -> str:
        return "swiglpk"
    
    @property
    def lp(self):
        """Get PolarsLP representation (lazy build)."""
        if self._lp is None:
            self._lp = LPBuilder(self.problem).build()
        return self._lp
    
    def solve(self) -> Solution:
        """Solves the linear programming problem."""
        problem = self.problem  # From BaseSolver
        
        if problem is None:
            return Solution(
                status="ERROR: No problem set",
                objective_value=None,
                variables={},
            )
        
        prob = None
        try:
            data = MatrixConverter.to_glpk(problem)
            variables_list = data["variables"]
            num_vars = len(variables_list)
            
            if problem.sense.lower() == "max":
                prob = swiglpk.glp_create_prob()
                swiglpk.glp_set_prob_name(prob, "LP")
                swiglpk.glp_set_obj_dir(prob, swiglpk.GLP_MAX)
            else:
                prob = swiglpk.glp_create_prob()
                swiglpk.glp_set_prob_name(prob, "LP")
                swiglpk.glp_set_obj_dir(prob, swiglpk.GLP_MIN)
            
            swiglpk.glp_add_cols(prob, num_vars)
            
            var_types = problem.variable_types if problem.variable_types else {}
            
            for i, var in enumerate(variables_list):
                swiglpk.glp_set_col_name(prob, i + 1, var)
                btype, lb, ub = data["col_bounds"][i]
                glp_type = getattr(swiglpk, f"GLP_{btype}")
                swiglpk.glp_set_col_bnds(prob, i + 1, glp_type, lb, ub)
                
                vtype = var_types.get(var, "continuous")
                if vtype == "integer":
                    swiglpk.glp_set_col_kind(prob, i + 1, swiglpk.GLP_IV)
                elif vtype == "binary":
                    swiglpk.glp_set_col_kind(prob, i + 1, swiglpk.GLP_BV)
                
                swiglpk.glp_set_obj_coef(prob, i + 1, data["objective"][i])
            
            num_constraints = len(problem.constraints)
            swiglpk.glp_add_rows(prob, num_constraints)
            
            for i in range(num_constraints):
                row_idx = i + 1
                swiglpk.glp_set_row_name(prob, row_idx, problem.constraints[i].name or f"R{i}")
                btype, lb, ub = data["row_bounds"][i]
                glp_type = getattr(swiglpk, f"GLP_{btype}")
                swiglpk.glp_set_row_bnds(prob, row_idx, glp_type, lb, ub)
            
            if data["ia"]:
                n = len(data["ia"])
                ia_arr = swiglpk.intArray(n + 1)
                ja_arr = swiglpk.intArray(n + 1)
                ar_arr = swiglpk.doubleArray(n + 1)
                for i in range(n):
                    ia_arr[i + 1] = data["ia"][i]
                    ja_arr[i + 1] = data["ja"][i]
                    ar_arr[i + 1] = data["ar"][i]
                swiglpk.glp_load_matrix(prob, n, ia_arr, ja_arr, ar_arr)
            
            smcp = swiglpk.glp_smcp()
            swiglpk.glp_init_smcp(smcp)
            if self.config.presolve:
                swiglpk.glp_scale_prob(prob, swiglpk.GLP_SF_AUTO)
            
            smcp.msg_lev = swiglpk.GLP_MSG_OFF if not self.config.verbose else swiglpk.GLP_MSG_ALL
            
            swiglpk.glp_simplex(prob, smcp)
            
            status = swiglpk.glp_get_status(prob)
            
            status_map = {
                swiglpk.GLP_OPT: "OPTIMAL",
                swiglpk.GLP_FEAS: "FEASIBLE",
                swiglpk.GLP_INFEAS: "INFEASIBLE",
                swiglpk.GLP_NOFEAS: "NOFEAS",
                swiglpk.GLP_UNBND: "UNBOUNDED",
                swiglpk.GLP_UNDEF: "UNDEFINED",
            }
            status_str = status_map.get(status, "UNKNOWN")
            
            variables = {}
            dual_values = {}
            reduced_costs = {}
            
            if status_str == "OPTIMAL":
                for i, var in enumerate(variables_list):
                    variables[var] = swiglpk.glp_get_col_prim(prob, i + 1)
                    rc = swiglpk.glp_get_col_dual(prob, i + 1)
                    if abs(rc) > 1e-10:
                        reduced_costs[var] = rc
                
                for i, constr in enumerate(problem.constraints):
                    pi = swiglpk.glp_get_row_dual(prob, i + 1)
                    if abs(pi) > 1e-10:
                        dual_values[constr.name or f"R{i}"] = pi
                
                obj_value = swiglpk.glp_get_obj_val(prob)
                try:
                    self._iterations = swiglpk.glp_get_simplex_itcnt(prob)
                except Exception as e:
                    self._iterations = 0
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"No se pudieron extraer iteraciones de GLPK: {e}")
            else:
                obj_value = None
            
            swiglpk.glp_delete_prob(prob)
            
            sensitivity = None
            try:
                from ..analysis.sensitivity import extract_glpk_sensitivity
                sensitivity = extract_glpk_sensitivity(prob, variables_list, problem.constraints)
            except Exception as e:
                if self.config.verbose:
                    print(f"Advertencia: No se pudo extraer sensibilidad de GLPK: {e}")
            
            self._solution = Solution(
                status=status_str,
                objective_value=obj_value,
                variables=variables,
                dual_values=dual_values if dual_values else None,
                reduced_costs=reduced_costs if reduced_costs else None,
                iterations=self._iterations,
                nodes=self._nodes,
                sensitivity=sensitivity,
            )
            
            return self._solution
            
        except Exception as e:
            if prob is not None:
                try:
                    swiglpk.glp_delete_prob(prob)
                except Exception as cleanup_err:
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"Error al limpiar problema GLPK: {cleanup_err}")
            
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
