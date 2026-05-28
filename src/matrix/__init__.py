"""
Módulo principal del paquete `matrix`. Aquí se pueden importar las clases
y funciones principales que se desean exponer a los usuarios del paquete.

"""

from .builder import LPBuilder
from .matrix import PolarsLP
from .converter import MatrixConverter

__all__ = [
    "LPBuilder",
    "PolarsLP",
    "MatrixConverter",
]
