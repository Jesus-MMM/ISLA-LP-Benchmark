"""
Solver HiGHS para problemas de programacion lineal.
Implementacion usando highspy (interfaz nativa a HiGHS).
"""

from typing import Optional

import highspy

from ..core import LinearProblem, Solution
from ..matrix import LPBuilder, MatrixConverter
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
        
        try:
            data = MatrixConverter.to_highs(problem)
            variables_list = data["variables"]
            
            hp = highspy.Highs()
            hp.setOptionValue("output_flag", False)
            
            for lb, ub in zip(data["col_lower"], data["col_upper"]):
                hp.addVar(lb, ub)
            
            for i, cost in enumerate(data["objective"]):
                if cost != 0:
                    hp.changeColCost(i, cost)
            
            for i in range(len(data["row_indices"])):
                hp.addRow(
                    data["row_lower"][i], data["row_upper"][i],
                    len(data["row_indices"][i]),
                    data["row_indices"][i], data["row_values"][i]
                )
            
            if problem.sense.lower() == "max":
                hp.changeObjectiveSense(highspy.ObjSense.kMaximize)
            
            hp.run()
            
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
            basis = None
            
            if status == "OPTIMAL":
                solution = hp.getSolution()
                for i, var in enumerate(variables_list):
                    variables[var] = solution.col_value[i]
                
                try:
                    for i, constr in enumerate(problem.constraints):
                        if i < len(solution.row_dual):
                            dual_values[constr.name or f"R{i}"] = solution.row_dual[i]
                except Exception as e:
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"No se pudieron extraer valores duales de HiGHS: {e}")
                
                try:
                    basis_info = hp.getBasis()
                    basis = {var: ("basic" if basis_info[i] == 0 else "nonbasic") 
                               for i, var in enumerate(variables_list)}
                except Exception as e:
                    basis = None
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"No se pudo obtener informacion de base HiGHS: {e}")
            
            try:
                from ..analysis.sensitivity import extract_highs_sensitivity
                extract_highs_sensitivity(hp)
            except Exception as e:
                if self.config.verbose:
                    print(f"Advertencia: No se pudo extraer sensibilidad de HiGHS: {e}")
            
            
            numerical_quality = None
            try:
                from ..core import NumericalQuality
                info = hp.getInfo()
                mip_gap = getattr(info, 'mip_gap', 0.0) or 0.0
                numerical_quality = NumericalQuality(
                    mip_gap=float(mip_gap),
                    nodes_per_second=float(getattr(info, 'node_count', 0) or 0),
                )
            except Exception:
                pass

            self._solution = Solution(
                status=status,
                objective_value=hp.getObjectiveValue() if status == "OPTIMAL" else None,
                variables=variables,
                dual_values=dual_values if dual_values else None,
                reduced_costs=reduced_costs if reduced_costs else None,
                basis=basis,
                numerical_quality=numerical_quality,
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