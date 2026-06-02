"""
Módulo core para el solver de programación lineal.
Soporta LP continuo y MILP (integer, binary).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .bound import VariableBound
from .constraint import LinearConstraint


@dataclass
class LinearProblem:
    """
    Representa un problema de programación lineal (LP) o MILP.

    ### Atributos:
    - objective: dict[str, float] - Coeficientes de la función objetivo.
    - sense: str - Dirección de optimización ("max" o "min").
    - constraints: list[LinearConstraint] - Lista de restricciones lineales.
    - variables: list[str] - Lista de nombres de variables.
    - bounds: dict[str, VariableBound] - Límites de cada variable.
    - name: str - Nombre opcional del problema.
    - variable_types: dict[str, str] - Tipos de variable ("continuous" | "integer" | "binary").
    - solver_hints: dict[str, Any] - Metadatos para solvers.
    """

    objective: dict[str, float]
    sense: str
    constraints: list[LinearConstraint]
    variables: list[str]
    bounds: dict[str, VariableBound]
    name: str = ""
    # NUEVOS CAMPOS PARA MILP
    variable_types: dict[str, str] = field(default_factory=dict)
    solver_hints: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Asigna "continuous" a variables sin tipo especificado."""
        for var in self.variables:
            if var not in self.variable_types:
                self.variable_types[var] = "continuous"

    @property
    def is_mip(self) -> bool:
        """Verifica si el problema es MIP (tiene variables no continuas)."""
        return any(vtype != "continuous" for vtype in self.variable_types.values())
