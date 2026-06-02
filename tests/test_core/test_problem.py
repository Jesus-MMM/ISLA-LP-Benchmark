"""
Tests for core dataclasses: LinearProblem, VariableBound, etc.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.bound import VariableBound
from src.core.constraint import LinearConstraint
from src.core.problem import LinearProblem


class TestLinearProblem:
    """Tests for LinearProblem dataclass."""

    def test_mip_detection(self):
        """Test is_mip property."""
        # Continuous-only problem
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=")],
            variables=["x"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=100)},
        )
        assert not problem.is_mip

        # Add integer variable
        problem.variable_types["x"] = "integer"
        assert problem.is_mip

    def test_default_continuous_types(self):
        """Test that variables default to continuous."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        assert problem.variable_types["x"] == "continuous"
        assert problem.variable_types["y"] == "continuous"

    def test_variable_bound_validation(self):
        """Test VariableBound validation."""
        # Valid bound
        bound = VariableBound(variable="x", lower=0, upper=10)
        assert bound.is_valid()

        # Invalid: lower > upper
        bound = VariableBound(variable="x", lower=10, upper=5)
        assert not bound.is_valid()

        # Binary must be in [0, 1]
        bound = VariableBound(variable="x", lower=-1, upper=1, variable_type="binary")
        assert not bound.is_valid()

    def test_empty_objective_raises_error(self):
        """Test empty objective raises error."""
        import pytest

        from src.parser.lp_parser import LPParser
        txt = "max: ;\nx >= 0;"
        with pytest.raises(ValueError, match="vacía"):
            LPParser(txt).parse()

    def test_is_mip_with_binary(self):
        """Test is_mip with binary variables."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
            variable_types={"x": "binary", "y": "continuous"},
        )
        assert problem.is_mip

    def test_custom_problem_name(self):
        """Test custom problem name."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=")],
            variables=["x"],
            bounds={},
            name="mi_problema",
        )
        assert problem.name == "mi_problema"

    def test_solver_hints_usage(self):
        """Test solver_hints dictionary."""
        hints = {"warm_start": True, "method": "barrier"}
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
            solver_hints=hints,
        )
        assert problem.solver_hints["warm_start"] is True
        assert problem.solver_hints["method"] == "barrier"

    def test_multiple_constraints(self):
        """Test problem with multiple constraints."""
        constraints = [
            LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<="),
            LinearConstraint(coefficients={"x": 1}, rhs=5, sense=">="),
            LinearConstraint(coefficients={"y": 1}, rhs=3, sense="="),
        ]
        problem = LinearProblem(
            objective={"x": 3, "y": 4},
            sense="max",
            constraints=constraints,
            variables=["x", "y"],
            bounds={},
        )
        assert len(problem.constraints) == 3
        assert problem.constraints[0].sense == "<="
        assert problem.constraints[1].sense == ">="
        assert problem.constraints[2].sense == "="

    def test_variable_types_default_in_post_init(self):
        """Test that variable_types is populated correctly in __post_init__."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["a", "b", "c"],
            bounds={},
        )
        for var in ["a", "b", "c"]:
            assert problem.variable_types[var] == "continuous"

    def test_is_mip_all_continuous(self):
        """Test is_mip returns False when all variables are continuous."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
            variable_types={"x": "continuous", "y": "continuous"},
        )
        assert not problem.is_mip

    def test_is_mip_mixed_types(self):
        """Test is_mip with mixed variable types."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2, "z": 3},
            sense="max",
            constraints=[],
            variables=["x", "y", "z"],
            bounds={},
            variable_types={"x": "continuous", "y": "integer", "z": "binary"},
        )
        assert problem.is_mip

    def test_no_constraints_allowed(self):
        """Test that LinearProblem can be created with empty constraints list."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        assert problem.constraints == []
