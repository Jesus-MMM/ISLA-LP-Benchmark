"""
Tests for core dataclasses: LinearProblem, VariableBound, etc.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.problem import LinearProblem
from src.core.constraint import LinearConstraint
from src.core.bound import VariableBound


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
