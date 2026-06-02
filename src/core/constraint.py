from dataclasses import dataclass


@dataclass
class LinearConstraint:
    """
    Representa una restricción lineal de la forma:
    
    a1*x1 + a2*x2 + ... + an*xn (<=, >=, =) b
    
    ### atributos:
    - coefficients: dict[str, float] - Coeficientes de las variables en la restricción.
    - rhs: float - Valor del lado derecho de la restricción.
    - sense: str - Tipo de restricción ("<=", ">=", "=").
    - name: str - Nombre de la restricción (autogenerado si no se da).
    """

    coefficients: dict[str, float]
    rhs: float
    sense: str  # "<=", ">=", "="
    name: str = ""  # Nuevo campo para identificación
