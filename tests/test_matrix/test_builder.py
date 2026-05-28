"""
Tests para LPBuilder.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import polars as pl
from src.core.problem import LinearProblem
from src.core.constraint import LinearConstraint
from src.core.bound import VariableBound
from src.matrix.builder import LPBuilder
from src.matrix.matrix import PolarsLP


class TestLPBuilder:
    """Tests para la clase LPBuilder."""

    def test_build_returns_polarslp(self):
        """Test que build() retorna un PolarsLP."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<="),
            ],
            variables=["x", "y"],
            bounds={
                "x": VariableBound("x", lower=0, upper=10),
                "y": VariableBound("y", lower=0, upper=5),
            },
        )
        builder = LPBuilder(problem)
        result = builder.build()
        assert isinstance(result, PolarsLP)

    def test_objective_dataframe(self):
        """Test DataFrame de la funcion objetivo."""
        problem = LinearProblem(
            objective={"x": 3, "y": 4},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        builder = LPBuilder(problem)
        result = builder.build()
        assert isinstance(result.objective, pl.DataFrame)
        assert result.objective.shape[0] == 2
        obj_dict = {r["variable"]: r["coefficient"] for r in result.objective.to_dicts()}
        assert obj_dict["x"] == 3.0
        assert obj_dict["y"] == 4.0

    def test_coefficients_dataframe(self):
        """Test DataFrame de coeficientes de restricciones."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 2, "y": 3}, rhs=10, sense="<="),
                LinearConstraint(coefficients={"x": 1}, rhs=5, sense=">="),
            ],
            variables=["x", "y"],
            bounds={},
        )
        result = LPBuilder(problem).build()
        assert isinstance(result.coefficients, pl.DataFrame)
        assert result.coefficients.shape[0] >= 3

    def test_constraints_dataframe(self):
        """Test DataFrame de definicion de restricciones."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<="),
            ],
            variables=["x"],
            bounds={},
        )
        result = LPBuilder(problem).build()
        assert isinstance(result.constraints, pl.DataFrame)
        assert result.constraints.shape[0] == 1
        row = result.constraints.to_dicts()[0]
        assert row["sense"] == "<="
        assert row["rhs"] == 10.0

    def test_bounds_dataframe(self):
        """Test DataFrame de limites de variables."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={
                "x": VariableBound("x", lower=0, upper=10),
                "y": VariableBound("y", lower=-5, upper=5),
            },
        )
        result = LPBuilder(problem).build()
        assert isinstance(result.bounds, pl.DataFrame)
        assert result.bounds.shape[0] == 2
        bounds_dict = {r["variable"]: r for r in result.bounds.to_dicts()}
        assert bounds_dict["x"]["lower"] == 0
        assert bounds_dict["x"]["upper"] == 10
        assert bounds_dict["y"]["lower"] == -5

    def test_sense_propagation(self):
        """Test que el sentido se propaga correctamente."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="min",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        result = LPBuilder(problem).build()
        assert result.sense == "min"

    def test_max_sense(self):
        """Test sentido maximizacion."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        result = LPBuilder(problem).build()
        assert result.sense == "max"

    def test_no_bounds(self):
        """Test construccion sin bounds."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        result = LPBuilder(problem).build()
        assert result.bounds.shape[0] == 0

    def test_no_constraints(self):
        """Test construccion sin restricciones."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        result = LPBuilder(problem).build()
        assert result.constraints.shape[0] == 0
        assert result.coefficients.shape[0] == 0

    def test_none_bounds(self):
        """Test bounds con valores None."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={"x": VariableBound("x", lower=None, upper=None)},
        )
        result = LPBuilder(problem).build()
        row = result.bounds.to_dicts()[0]
        assert row["lower"] is None
        assert row["upper"] is None
