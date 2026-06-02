"""
Generador de problemas de programación lineal sintéticos.
"""

import random

from ..core import LinearConstraint, LinearProblem, VariableBound


class ProblemGenerator:
    """
    Genera problemas de PL/MILP sintéticos con características controladas.

    Args:
        random_state: int | None - Semilla para reproducibilidad.
    """

    def __init__(self, random_state: int | None = None) -> None:
        self._rng = random.Random(random_state)

    def generate_lp(
        self,
        n_vars: int = 5,
        n_constraints: int = 10,
        density: float = 0.3,
        coeff_range: tuple[float, float] = (-10.0, 10.0),
        sense: str = "max",
    ) -> LinearProblem:
        """
        Genera un problema de PL continuo aleatorio.

        Args:
            n_vars: Número de variables.
            n_constraints: Número de restricciones.
            density: Densidad de la matriz de coeficientes (0.0 a 1.0).
            coeff_range: Rango (mín, máx) para coeficientes.
            sense: "max" o "min".

        Returns:
            LinearProblem: Problema generado.
        """
        variables = [f"x{i+1}" for i in range(n_vars)]

        objective: dict[str, float] = {}
        for var in variables:
            if self._rng.random() < 0.8:
                objective[var] = self._rng.uniform(*coeff_range)

        if not objective:
            objective[variables[0]] = 1.0

        constraints: list[LinearConstraint] = []
        for i in range(n_constraints):
            coeffs: dict[str, float] = {}
            for var in variables:
                if self._rng.random() < density:
                    coeffs[var] = self._rng.uniform(*coeff_range)
            if not coeffs:
                coeffs[variables[self._rng.randint(0, n_vars - 1)]] = 1.0

            rhs = self._rng.uniform(1.0, 100.0)
            sense_op = self._rng.choice(["<=", ">=", "="])
            constraints.append(LinearConstraint(
                coefficients=coeffs,
                rhs=rhs,
                sense=sense_op,
                name=f"C{i+1}",
            ))

        bounds: dict[str, VariableBound] = {}
        for var in variables:
            lo = self._rng.uniform(0, 10)
            up = lo + self._rng.uniform(1, 50)
            bounds[var] = VariableBound(variable=var, lower=lo, upper=up)

        return LinearProblem(
            objective=objective,
            sense=sense,
            constraints=constraints,
            variables=variables,
            bounds=bounds,
        )

    def generate_milp(
        self,
        n_vars: int = 5,
        n_constraints: int = 10,
        n_int_vars: int = 2,
        density: float = 0.3,
        coeff_range: tuple[float, float] = (-10.0, 10.0),
        sense: str = "max",
    ) -> LinearProblem:
        """
        Genera un problema MILP aleatorio.

        Args:
            n_vars: Número de variables.
            n_constraints: Número de restricciones.
            n_int_vars: Número de variables enteras.
            density: Densidad de la matriz de coeficientes.
            coeff_range: Rango para coeficientes.
            sense: "max" o "min".

        Returns:
            LinearProblem: Problema MILP generado.
        """
        problem = self.generate_lp(
            n_vars=n_vars,
            n_constraints=n_constraints,
            density=density,
            coeff_range=coeff_range,
            sense=sense,
        )

        int_vars = self._rng.sample(problem.variables, min(n_int_vars, n_vars))
        for var in int_vars:
            problem.variable_types[var] = "integer"

        return problem

    def generate_netlib_like(self, name: str = "afiro") -> LinearProblem:
        """
        Genera un problema con características similares a problemas Netlib.

        Args:
            name: Nombre del problema Netlib de referencia.

        Returns:
            LinearProblem: Problema generado.
        """
        profiles = {
            "afiro": (32, 27, 0.05),
            "kb2": (41, 43, 0.04),
            "sc50a": (50, 48, 0.03),
            "sc50b": (50, 48, 0.03),
            "adlittle": (97, 56, 0.02),
        }
        params = profiles.get(name, (50, 50, 0.04))
        return self.generate_lp(
            n_vars=params[0],
            n_constraints=params[1],
            density=params[2],
            coeff_range=(-10.0, 10.0),
        )

    def generate_ill_conditioned(self) -> LinearProblem:
        """
        Genera un problema mal condicionado para stress testing.

        Returns:
            LinearProblem con matriz mal condicionada.
        """
        n_vars = 10
        n_constraints = 10
        variables = [f"x{i+1}" for i in range(n_vars)]

        objective = {f"x{i+1}": 1.0 for i in range(n_vars)}

        constraints: list[LinearConstraint] = []
        for i in range(n_constraints):
            coeffs: dict[str, float] = {}
            for j in range(n_vars):
                if i == j:
                    coeffs[f"x{j+1}"] = 1.0
                elif j < i:
                    coeffs[f"x{j+1}"] = 1e6
                else:
                    coeffs[f"x{j+1}"] = 1e-6
            constraints.append(LinearConstraint(
                coefficients=coeffs,
                rhs=1000.0,
                sense="<=",
                name=f"IC{i+1}",
            ))

        bounds: dict[str, VariableBound] = {}
        for var in variables:
            bounds[var] = VariableBound(variable=var, lower=0.0, upper=1e6)

        return LinearProblem(
            objective=objective,
            sense="max",
            constraints=constraints,
            variables=variables,
            bounds=bounds,
        )
