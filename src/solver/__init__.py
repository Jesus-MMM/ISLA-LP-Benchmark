"""
Modulo de solvers para programacion lineal.
Proporciona interfaz abstracta y implementaciones concretas.
"""

from .base import BaseSolver, SolverStats, SolverRegistry, register_solver
from .gurobi import GurobiSolver
from .multi_solver import MultiSolver, MultiSolverResult, ProblemResult
from .benchmark import BenchmarkRunner, BenchmarkResult, BenchmarkConfig, run_quick_benchmark

SolverLP = None
try:
    from .gurobi import GurobiSolver
    # Instanciar con problema=None solo para validacion de disponibilidad
    # Nota: GurobiSolver(None) funciona porque BaseSolver acepta None en el constructor si se maneja
    if GurobiSolver(None).is_available:
        SolverLP = GurobiSolver
    else:
        # buscar primer solver disponible en el registro
        available_solvers = SolverRegistry.list_solvers(available_only=True)
        if available_solvers:
            # Priorizar solvers robustos (HiGHS, CBC, GLPK)
            priority = ["highs", "cbc", "glpk", "scip"]
            for p in priority:
                if p in available_solvers:
                    SolverLP = SolverRegistry.get(p)
                    break
            # Si ninguno de los prioritarios está, usar el primero disponible
            if SolverLP is None:
                SolverLP = SolverRegistry.get(available_solvers[0])
        else:
            # Fallback final
            SolverLP = GurobiSolver
except ImportError:
    SolverLP = GurobiSolver

SolverConfig = BaseSolver.Config


SolverRegistry.register("gurobi", GurobiSolver, available=True)

try:
    from .highs_solver import HiGHSSolver
    SolverRegistry.register("highs", HiGHSSolver, available=True)
except ImportError as e:
    class HiGHSSolver:
        pass
    HiGHSSolver.solver_name = "highs"
    HiGHSSolver.__name__ = "HiGHSSolver"
    SolverRegistry.register("highs", HiGHSSolver, available=False)
    SolverRegistry.set_unavailable("highs", f"highspy not available: {e}")

try:
    from .glpk_solver import GLPKSolver
    SolverRegistry.register("glpk", GLPKSolver, available=True)
except ImportError as e:
    class GLPKSolver:
        pass
    GLPKSolver.solver_name = "glpk"
    GLPKSolver.__name__ = "GLPKSolver"
    SolverRegistry.register("glpk", GLPKSolver, available=False)
    SolverRegistry.set_unavailable("glpk", f"swiglpk not available: {e}")

try:
    from .cbc import CBCSolver
    import pulp
    if "PULP_CBC_CMD" in pulp.listSolvers():
        SolverRegistry.register("cbc", CBCSolver, available=True)
    else:
        SolverRegistry.register("cbc", CBCSolver, available=False)
        SolverRegistry.set_unavailable("cbc", "PULP_CBC_CMD not found")
except ImportError as e:
    class CBCSolver:
        pass
    CBCSolver.solver_name = "cbc"
    CBCSolver.__name__ = "CBCSolver"
    SolverRegistry.register("cbc", CBCSolver, available=False)
    SolverRegistry.set_unavailable("cbc", f"not available: {e}")

# F4-3: Register SCIP solver
try:
    from .scip import SCIPSolver
    SolverRegistry.register("scip", SCIPSolver, available=True)
except ImportError as e:
    class SCIPSolver:
        pass
    SCIPSolver.solver_name = "scip"
    SCIPSolver.__name__ = "SCIPSolver"
    SolverRegistry.register("scip", SCIPSolver, available=False)
    SolverRegistry.set_unavailable("scip", f"pyscipopt not available: {e}")

# F7-1: Register ECOS solver
try:
    from .ecos import ECOSSolver, _is_solver_available as _ecos_avail
    SolverRegistry.register("ecos", ECOSSolver, available=_ecos_avail)
    if not _ecos_avail:
        SolverRegistry.set_unavailable("ecos", "ecos package not installed")
except ImportError as e:
    class ECOSSolver:
        pass
    ECOSSolver.solver_name = "ecos"
    ECOSSolver.__name__ = "ECOSSolver"
    SolverRegistry.register("ecos", ECOSSolver, available=False)
    SolverRegistry.set_unavailable("ecos", f"ecos not available: {e}")

# F7-2: Register OSQP solver
try:
    from .osqp_solver import OSQPSolver, _is_solver_available as _osqp_avail
    SolverRegistry.register("osqp", OSQPSolver, available=_osqp_avail)
    if not _osqp_avail:
        SolverRegistry.set_unavailable("osqp", "osqp package not installed")
except ImportError as e:
    class OSQPSolver:
        pass
    OSQPSolver.solver_name = "osqp"
    OSQPSolver.__name__ = "OSQPSolver"
    SolverRegistry.register("osqp", OSQPSolver, available=False)
    SolverRegistry.set_unavailable("osqp", f"osqp not available: {e}")

# F7-3: Register CVXOPT solver
try:
    from .cvxopt_solver import CVXOPTSolver, _is_solver_available as _cvxopt_avail
    SolverRegistry.register("cvxopt", CVXOPTSolver, available=_cvxopt_avail)
    if not _cvxopt_avail:
        SolverRegistry.set_unavailable("cvxopt", "cvxopt package not installed")
except ImportError as e:
    class CVXOPTSolver:
        pass
    CVXOPTSolver.solver_name = "cvxopt"
    CVXOPTSolver.__name__ = "CVXOPTSolver"
    SolverRegistry.register("cvxopt", CVXOPTSolver, available=False)
    SolverRegistry.set_unavailable("cvxopt", f"cvxopt not available: {e}")

# F7-4: Register SCS solver
try:
    from .scs_solver import SCSSolver, _is_solver_available as _scs_avail
    SolverRegistry.register("scs", SCSSolver, available=_scs_avail)
    if not _scs_avail:
        SolverRegistry.set_unavailable("scs", "scs package not installed")
except ImportError as e:
    class SCSSolver:
        pass
    SCSSolver.solver_name = "scs"
    SCSSolver.__name__ = "SCSSolver"
    SolverRegistry.register("scs", SCSSolver, available=False)
    SolverRegistry.set_unavailable("scs", f"scs not available: {e}")

# F7-5: Register Ipopt solver (via CasADi)
try:
    from .ipopt_solver import IpoptSolver, _is_solver_available as _ipopt_avail
    SolverRegistry.register("ipopt", IpoptSolver, available=_ipopt_avail)
    if not _ipopt_avail:
        SolverRegistry.set_unavailable("ipopt", "casadi package not installed")
except ImportError as e:
    class IpoptSolver:
        pass
    IpoptSolver.solver_name = "ipopt"
    IpoptSolver.__name__ = "IpoptSolver"
    SolverRegistry.register("ipopt", IpoptSolver, available=False)
    SolverRegistry.set_unavailable("ipopt", f"casadi not available: {e}")


__all__ = [
    "BaseSolver",
    "SolverStats", 
    "SolverRegistry",
    "register_solver",
    "GurobiSolver",
    "CBCSolver",
    "HiGHSSolver",
    "GLPKSolver",
    "ECOSSolver",
    "OSQPSolver",
    "CVXOPTSolver",
    "SCSSolver",
    "IpoptSolver",
    "SolverLP",
    "SolverConfig",
    "MultiSolver",
    "MultiSolverResult", 
    "ProblemResult",
    "BenchmarkRunner",
    "BenchmarkResult",
    "BenchmarkConfig",
    "run_quick_benchmark"
]