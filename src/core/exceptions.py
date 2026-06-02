"""
Excepciones personalizadas para programación lineal.
"""


class LPError(Exception):
    """Excepción base para errores relacionados con PL."""

    def __init__(self, message: str, problem: str | None = None):
        self.problem = problem
        super().__init__(message)


class LPParseError(LPError):
    """Error al parsear un problema de PL."""

    def __init__(self, message: str, line: int | None = None, problem: str | None = None):
        self.line = line
        full_message = "Error de parseo"
        if line is not None:
            full_message += f" en línea {line}"
        full_message += f": {message}"
        super().__init__(full_message, problem)


class LPInfeasibleError(LPError):
    """El problema de PL es infactible."""

    def __init__(self, problem: str | None = None):
        super().__init__(
            "El problema es infactible: ninguna solución satisface todas las restricciones.",
            problem
        )


class LPUnboundedError(LPError):
    """El problema de PL es no acotado."""

    def __init__(self, problem: str | None = None):
        super().__init__(
            "El problema es no acotado: el objetivo puede mejorar indefinidamente.",
            problem
        )


class LPUnsolvedError(LPError):
    """Error al intentar acceder a la solución sin resolver."""

    def __init__(self, message: str = "El problema no ha sido resuelto"):
        super().__init__(message)


class LPVisualizationError(LPError):
    """Error al generar visualización."""

    def __init__(self, message: str):
        super().__init__(f"Error de visualización: {message}")


class LPConfigurationError(LPError):
    """Error de configuración."""

    def __init__(self, message: str):
        super().__init__(f"Error de configuración: {message}")
