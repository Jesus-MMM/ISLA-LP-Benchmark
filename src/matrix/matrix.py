"""
Definición de tipos para matrices Polars.
"""

from dataclasses import dataclass

import polars as pl


@dataclass
class PolarsLP:
    """
    Estructura de datos Polars para un problema de PL.

    ### atributos:
    - objective: pl.DataFrame - Coeficientes de la función objetivo.
    - coefficients: pl.DataFrame - Matriz de coeficientes de restricciones.
    - constraints: pl.DataFrame - Definición de restricciones.
    - bounds: pl.DataFrame - Límites de variables.
    - sense: str - Dirección de optimización ("max" o "min").
    """

    objective: pl.DataFrame
    coefficients: pl.DataFrame
    constraints: pl.DataFrame
    bounds: pl.DataFrame
    sense: str
