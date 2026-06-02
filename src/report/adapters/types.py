from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReportData:
    """Contenedor de datos extraidos de objetos de dominio LP.

    Attributes:
        variables: Pares clave-valor para sustitucion de {{variable}} en plantillas.
        tables: Nombre de tabla a (encabezados, filas) para inyeccion programatica.
        images: ID de imagen a ruta de archivo para referencias de graficos.
    """
    variables: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, tuple[list[str], list[list[str]]]] = field(default_factory=dict)
    images: dict[str, str] = field(default_factory=dict)
