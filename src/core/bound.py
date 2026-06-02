from dataclasses import dataclass


@dataclass
class VariableBound:
    """
    Representa los límites de una variable.
    
    ### atributos:
    - variable: str - Nombre de la variable.
    - lower: float | None - Límite inferior (None = sin límite).
    - upper: float | None - Límite superior (None = sin límite).
    - variable_type: str - Tipo de variable ("continuous", "integer", "binary").
    """

    variable: str
    lower: float | None = None
    upper: float | None = None
    variable_type: str = "continuous"  # NUEVO

    def is_valid(self) -> bool:
        """Verifica si los límites son válidos según el tipo de variable."""
        # Validar que lower <= upper si ambos están definidos
        if self.lower is not None and self.upper is not None:
            if self.lower > self.upper:
                return False

        # Validar variables binarias (deben estar en [0, 1])
        if self.variable_type == "binary":
            if self.lower is not None and self.lower < 0:
                return False
            if self.upper is not None and self.upper > 1:
                return False

        return True
