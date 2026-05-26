"""
Clase base abstracta para solvers de programacion lineal.
Proporciona una interfaz comun para diferentes implementaciones de solvers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ..core import Solution, LinearProblem
from ..core.solution import ProgressPoint as PP

# Alias for type hints
ProgressPoint = PP


@dataclass
class SolverStats:
    """Estadísticas de la ejecución del solver."""
    solve_time: float = 0.0
    build_time: float = 0.0
    iterations: int = 0
    nodes: int = 0
    simplex_iterations: int = 0
    barrier_iterations: int = 0
    crossover_iterations: int = 0
    memory_used_mb: float = 0.0
    # NUEVOS CAMPOS PARA CALIDAD NUMÉRICA Y PROGRESO
    max_bound_viol: float = 0.0
    max_constraint_viol: float = 0.0
    condition_number: Optional[float] = None
    progress_log: Optional[list[ProgressPoint]] = None

@dataclass
class SolverCapabilities:
    """Capacidades explicitas de un solver."""
    lp: bool = True
    milp: bool = True
    qp: bool = False
    duals: bool = True
    warm_start: bool = False
    sensitivity: bool = False


class BaseSolver(ABC):
    """
    Clase base abstracta para solvers de programación lineal.
    
    Define la interfaz común que todos los solvers deben implementar.
    Todos los solvers deben aceptar LinearProblem en su constructor.
    """
    
    @dataclass
    class Config:
        """Configuración base del solver."""
        verbose: bool = False
        time_limit: Optional[float] = None
        mip_gap: Optional[float] = None
        threads: Optional[int] = None
        presolve: int = 1  # 1=auto, 0=off, -1=conservative (flexible para solvers)
        seed: Optional[int] = None
    
    def __init__(self, problem: LinearProblem, config: Optional[Config] = None):
        """
        Inicializa el solver con el problema y configuración proporcionados.
        
        Args:
            problem: El problema LP a resolver
            config: Configuración del solver. Si es None, usa configuración por defecto.
        """
        self.problem = problem
        self.config = config or self.Config()
        self.stats = SolverStats()
        self._solver_name = "BaseSolver"
        self.capabilities = SolverCapabilities()
    
    @property
    def solver_name(self) -> str:
        """Nombre del solver."""
        return self._solver_name
    
    @property
    def solver_version(self) -> str:
        """Version del solver."""
        return "0.0.0"
    
    @property
    def is_available(self) -> bool:
        """Verifica si el solver esta disponible."""
        return True
    
    @abstractmethod
    def solve(self) -> Solution:
        """
        Resuelve el problema de programacion lineal.
        
        Returns:
            Solution: Objeto con el estado, valores y metadatos de la solucion.
            
        Raises:
            NotImplementedError: Debe ser implementado por subclasses.
        """
        raise NotImplementedError("Subclasses must implement solve()")
    
    def reset(self) -> None:
        """Reinicia el estado del solver."""
        self.stats = SolverStats()
    
    def get_stats(self) -> SolverStats:
        """
        Obtiene las estadisticas de la ultima ejecucion.
        
        Returns:
            SolverStats: Objeto con las estadisticas del solver.
        """
        return self.stats
    
    def __repr__(self) -> str:
        return f"{self.solver_name} v{self.solver_version}(available={self.is_available})"


class SolverRegistry:
    """Registro de solvers disponibles."""
    
    _solvers: dict[str, type[BaseSolver]] = {}
    _availability: dict[str, bool] = {}
    _errors: dict[str, str] = {}
    
    @classmethod
    def register(cls, name: str, solver_class: type[BaseSolver], available: bool = True) -> None:
        """Registra un solver."""
        name = name.lower()
        cls._solvers[name] = solver_class
        cls._availability[name] = available
        cls._errors[name] = ""
    
    @classmethod
    def set_unavailable(cls, name: str, error: str = "") -> None:
        """Marca un solver como no disponible."""
        name = name.lower()
        cls._availability[name] = False
        cls._errors[name] = error
    
    @classmethod
    def is_available(cls, name: str) -> bool:
        """Verifica si un solver esta disponible."""
        return cls._availability.get(name.lower(), False)
    
    @classmethod
    def get_error(cls, name: str) -> str:
        """Obtiene el error de un solver."""
        return cls._errors.get(name.lower(), "")
    
    @classmethod
    def get(cls, name: str) -> Optional[type[BaseSolver]]:
        """Obtiene una clase de solver por nombre."""
        return cls._solvers.get(name.lower())
    
    @classmethod
    def list_solvers(cls, available_only: bool = False) -> list[str]:
        """Lista todos los solvers registrados."""
        if available_only:
            return [k for k, v in cls._availability.items() if v]
        return list(cls._solvers.keys())
    
    @classmethod
    def list_all_info(cls) -> dict:
        """Lista informacion de todos los solvers."""
        return {
            name: {
                "available": cls._availability.get(name, False),
                "error": cls._errors.get(name, ""),
            }
            for name in cls._solvers.keys()
        }
    
    @classmethod
    def create_solver(cls, name: str, **kwargs) -> Optional[BaseSolver]:
        """Crea una instancia de un solver por nombre."""
        solver_class = cls.get(name)
        if solver_class:
            return solver_class(**kwargs)
        return None


def register_solver(name: str):
    """Decorador para registrar automaticamente un solver."""
    def decorator(cls: type[BaseSolver]):
        SolverRegistry.register(name, cls)
        return cls
    return decorator
