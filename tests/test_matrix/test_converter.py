"""Tests para MatrixConverter."""

import numpy as np
import pytest

from src.core import LinearProblem, LinearConstraint, VariableBound
from src.matrix.converter import MatrixConverter


@pytest.fixture
def small_problem():
    """Problema pequeño: max 3x + 2y, x + y <= 10, 2x + y <= 15, x,y >= 0."""
    return LinearProblem(
        objective={"x": 3, "y": 2},
        sense="max",
        variables=["x", "y"],
        constraints=[
            LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<=", name="R1"),
            LinearConstraint(coefficients={"x": 2, "y": 1}, rhs=15, sense="<=", name="R2"),
        ],
        bounds={
            "x": VariableBound("x", 0, None),
            "y": VariableBound("y", 0, None),
        },
    )


@pytest.fixture
def milp_problem():
    """Problema MILP con variables mixtas."""
    return LinearProblem(
        objective={"x": 3, "y": 2, "z": 1},
        sense="min",
        variables=["x", "y", "z"],
        constraints=[
            LinearConstraint(coefficients={"x": 1, "y": 2, "z": 1}, rhs=20, sense="<=", name="C1"),
            LinearConstraint(coefficients={"x": 2, "y": 1, "z": 3}, rhs=30, sense=">=", name="C2"),
            LinearConstraint(coefficients={"x": 1, "y": 1, "z": 1}, rhs=10, sense="=", name="C3"),
        ],
        bounds={
            "x": VariableBound("x", 0, 10),
            "y": VariableBound("y", 0, None),
            "z": VariableBound("z", None, None, variable_type="integer"),
        },
        variable_types={"x": "continuous", "y": "continuous", "z": "integer"},
    )


class TestToHighs:
    def test_basic_structure(self, small_problem):
        result = MatrixConverter.to_highs(small_problem)
        assert "variables" in result
        assert "objective" in result
        assert "col_lower" in result
        assert "col_upper" in result
        assert "row_lower" in result
        assert "row_upper" in result
        assert "row_indices" in result
        assert "row_values" in result

    def test_objective(self, small_problem):
        result = MatrixConverter.to_highs(small_problem)
        np.testing.assert_array_almost_equal(result["objective"], [3.0, 2.0])

    def test_col_bounds(self, small_problem):
        result = MatrixConverter.to_highs(small_problem)
        np.testing.assert_array_almost_equal(result["col_lower"], [0.0, 0.0])
        assert result["col_upper"][0] > 1e20
        assert result["col_upper"][1] > 1e20

    def test_row_bounds(self, small_problem):
        result = MatrixConverter.to_highs(small_problem)
        np.testing.assert_array_almost_equal(result["row_upper"], [10.0, 15.0])
        assert result["row_lower"][0] < -1e20

    def test_matrix(self, small_problem):
        result = MatrixConverter.to_highs(small_problem)
        assert result["row_indices"][0] == [0, 1]
        assert result["row_values"][0] == [1.0, 1.0]

    def test_sense(self, small_problem):
        result = MatrixConverter.to_highs(small_problem)
        assert result["sense"] == "max"

    def test_milp_variable_types(self, milp_problem):
        result = MatrixConverter.to_highs(milp_problem)
        assert result["variable_types"] == {"x": "continuous", "y": "continuous", "z": "integer"}

    def test_equality_constraint(self, milp_problem):
        result = MatrixConverter.to_highs(milp_problem)
        assert result["row_lower"][2] == 10.0
        assert result["row_upper"][2] == 10.0


class TestToGlpk:
    def test_basic_structure(self, small_problem):
        result = MatrixConverter.to_glpk(small_problem)
        assert "variables" in result
        assert "objective" in result
        assert "col_bounds" in result
        assert "row_bounds" in result
        assert "ia" in result
        assert "ja" in result
        assert "ar" in result

    def test_objective(self, small_problem):
        result = MatrixConverter.to_glpk(small_problem)
        assert result["objective"] == [3.0, 2.0]

    def test_col_bounds(self, small_problem):
        result = MatrixConverter.to_glpk(small_problem)
        assert result["col_bounds"][0] == ("LO", 0.0, 0.0)
        assert result["col_bounds"][1] == ("LO", 0.0, 0.0)

    def test_row_bounds(self, small_problem):
        result = MatrixConverter.to_glpk(small_problem)
        assert result["row_bounds"][0] == ("UP", 0.0, 10.0)
        assert result["row_bounds"][1] == ("UP", 0.0, 15.0)

    def test_triplet_1indexed(self, small_problem):
        result = MatrixConverter.to_glpk(small_problem)
        assert all(i >= 1 for i in result["ia"])
        assert all(j >= 1 for j in result["ja"])
        assert len(result["ia"]) == 4
        assert len(result["ar"]) == 4

    def test_equality_row_bound(self, milp_problem):
        result = MatrixConverter.to_glpk(milp_problem)
        assert result["row_bounds"][2] == ("FX", 10.0, 10.0)

    def test_free_bound(self, milp_problem):
        result = MatrixConverter.to_glpk(milp_problem)
        assert result["col_bounds"][2] == ("FR", 0.0, 0.0)  # z has no bounds


class TestToCvxopt:
    def test_basic_structure(self, small_problem):
        result = MatrixConverter.to_cvxopt(small_problem)
        assert "c" in result
        assert "G" in result
        assert "h" in result

    def test_max_to_min(self, small_problem):
        """CVXOPT minimiza por defecto, objetivo max debe negarse."""
        result = MatrixConverter.to_cvxopt(small_problem)
        np.testing.assert_array_almost_equal(result["c"], [-3.0, -2.0])

    def test_inequality_matrix(self, small_problem):
        result = MatrixConverter.to_cvxopt(small_problem)
        assert result["G"] is not None
        assert result["h"] is not None
        assert result["A"] is None  # No equality constraints

    def test_equality_included(self, milp_problem):
        result = MatrixConverter.to_cvxopt(milp_problem)
        assert result["A"] is not None
        assert len(result["A"]) == 1  # One equality constraint

    def test_constraint_order(self, small_problem):
        result = MatrixConverter.to_cvxopt(small_problem)
        assert result["constraint_order"] == ["R1", "R2"]


class TestToOsqp:
    def test_basic_structure(self, small_problem):
        result = MatrixConverter.to_osqp(small_problem)
        assert "P" in result
        assert "q" in result
        assert "A" in result
        assert "l" in result
        assert "u" in result

    def test_zero_hessian(self, small_problem):
        result = MatrixConverter.to_osqp(small_problem)
        assert result["P"].shape == (2, 2)

    def test_linear_objective(self, small_problem):
        result = MatrixConverter.to_osqp(small_problem)
        np.testing.assert_array_almost_equal(result["q"], [-3.0, -2.0])  # negated for max

    def test_constraint_matrix_shape(self, small_problem):
        result = MatrixConverter.to_osqp(small_problem)
        expected_rows = 2 + 2  # 2 constraints + 2 variable bounds
        assert result["A"].shape == (expected_rows, 2)

    def test_inf_bounds(self, small_problem):
        result = MatrixConverter.to_osqp(small_problem)
        assert np.isneginf(result["l"][0])  # First constraint has -inf lower
        assert not np.isinf(result["l"][2])  # x >= 0 is finite


class TestToScipy:
    def test_basic_structure(self, small_problem):
        result = MatrixConverter.to_scipy(small_problem)
        assert "c" in result
        assert "A_ub" in result
        assert "b_ub" in result

    def test_max_to_min(self, small_problem):
        result = MatrixConverter.to_scipy(small_problem)
        np.testing.assert_array_almost_equal(result["c"], [-3.0, -2.0])

    def test_inequality(self, small_problem):
        result = MatrixConverter.to_scipy(small_problem)
        assert result["A_ub"] is not None
        assert result["b_ub"] is not None
        assert result["A_eq"] is None

    def test_equality_separated(self, milp_problem):
        result = MatrixConverter.to_scipy(milp_problem)
        assert result["A_eq"] is not None
        assert result["A_ub"] is not None  # Still has <= and >= constraints

    def test_bounds_tuple(self, small_problem):
        result = MatrixConverter.to_scipy(small_problem)
        assert result["bounds"] == [(0.0, None), (0.0, None)]

    def test_geq_converted_to_leq(self, milp_problem):
        """>= constraint should be negated to <= in scipy format."""
        result = MatrixConverter.to_scipy(milp_problem)
        assert result["A_ub"] is not None
        c2_row = result["A_ub"].toarray()[1]
        np.testing.assert_array_almost_equal(c2_row, [-2.0, -1.0, -3.0])
