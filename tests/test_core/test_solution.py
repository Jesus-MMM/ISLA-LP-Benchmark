"""
Tests for Solution and SolutionTable.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.solution import Solution, NumericalQuality


class TestSolution:
    """Tests for Solution dataclass."""
    
    def test_is_optimal(self):
        """Test is_optimal method."""
        sol = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 5.0})
        assert sol.is_optimal()
        
        sol2 = Solution(status="INFEASIBLE", objective_value=None, variables={})
        assert not sol2.is_optimal()
    
    def test_is_optimal_with_tolerance(self):
        """Test is_optimal with tolerance status."""
        sol = Solution(status="OPTIMAL (TOLERANCE)", objective_value=10.0, variables={"x": 5.0})
        assert sol.is_optimal()
    
    def test_numerical_quality(self):
        """Test NumericalQuality dataclass."""
        nq = NumericalQuality(
            max_bound_viol=1e-7,
            max_constraint_viol=1e-8,
            condition_number=100.0
        )
        assert nq.max_bound_viol == 1e-7
