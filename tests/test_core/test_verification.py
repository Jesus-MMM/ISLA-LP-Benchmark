"""
Tests para verificacion de soluciones: verify_solution y compare_solutions.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.bound import VariableBound
from src.core.constraint import LinearConstraint
from src.core.problem import LinearProblem
from src.core.solution import Solution
from src.core.verification import compare_solutions, verify_solution


class TestVerifySolution:
    """Tests para verify_solution."""

    def test_valid_solution(self):
        """Test solucion valida satisface todas las restricciones."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<="),
            ],
            variables=["x"],
            bounds={"x": VariableBound("x", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=5.0, variables={"x": 5.0})
        is_valid, issues = verify_solution(problem, solution)
        assert is_valid
        assert issues == []

    def test_violates_upper_bound(self):
        """Test violacion de limite superior."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={"x": VariableBound("x", lower=0, upper=5)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 10.0})
        is_valid, issues = verify_solution(problem, solution)
        assert not is_valid
        assert any("upper bound" in i for i in issues)

    def test_violates_lower_bound(self):
        """Test violacion de limite inferior."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={"x": VariableBound("x", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=-5.0, variables={"x": -5.0})
        is_valid, issues = verify_solution(problem, solution)
        assert not is_valid
        assert any("lower bound" in i for i in issues)

    def test_no_variables_in_solution(self):
        """Test solucion sin variables."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=None, variables={})
        is_valid, issues = verify_solution(problem, solution)
        assert not is_valid

    def test_constraint_less_equal_violated(self):
        """Test violacion de restriccion <=."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=5, sense="<="),
            ],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 10.0})
        is_valid, issues = verify_solution(problem, solution)
        assert not is_valid
        assert any("violated" in i for i in issues)

    def test_constraint_greater_equal_violated(self):
        """Test violacion de restriccion >=."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense=">="),
            ],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=3.0, variables={"x": 3.0})
        is_valid, issues = verify_solution(problem, solution)
        assert not is_valid
        assert any("violated" in i for i in issues)

    def test_constraint_equal_violated(self):
        """Test violacion de restriccion =."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="="),
            ],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=5.0, variables={"x": 5.0})
        is_valid, issues = verify_solution(problem, solution)
        assert not is_valid
        assert any("violated" in i for i in issues)

    def test_custom_tolerance(self):
        """Test tolerancia personalizada."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<="),
            ],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=10.000001, variables={"x": 10.000001})
        is_valid, _ = verify_solution(problem, solution, tolerance=1e-3)
        assert is_valid


class TestCompareSolutions:
    """Tests para compare_solutions."""

    def test_single_solution(self):
        """Test con una sola solucion (sin advertencias)."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        sol = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 10.0})
        warnings = compare_solutions(problem, [sol])
        assert warnings == []

    def test_two_optimal_agree(self):
        """Test dos soluciones optimas coinciden."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        sol1 = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 10.0})
        sol2 = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 10.0})
        warnings = compare_solutions(problem, [sol1, sol2])
        assert warnings == []

    def test_two_optimal_differ(self):
        """Test dos soluciones optimas con valores diferentes."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        sol1 = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 10.0})
        sol2 = Solution(status="OPTIMAL", objective_value=100.0, variables={"x": 100.0})
        warnings = compare_solutions(problem, [sol1, sol2])
        assert len(warnings) > 0
        assert any("differ" in w for w in warnings)

    def test_non_optimal_ignored(self):
        """Test que soluciones no optimas se ignoran en comparacion."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        sol1 = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 10.0})
        sol2 = Solution(status="INFEASIBLE", objective_value=None, variables={})
        warnings = compare_solutions(problem, [sol1, sol2])
        assert warnings == []

    def test_none_objective_values(self):
        """Test con valores objetivo None."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        sol1 = Solution(status="OPTIMAL", objective_value=None, variables={"x": 1.0})
        sol2 = Solution(status="OPTIMAL", objective_value=None, variables={"x": 2.0})
        warnings = compare_solutions(problem, [sol1, sol2])
        assert warnings == []

    def test_custom_tolerance(self):
        """Test comparacion con tolerancia personalizada."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        sol1 = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 10.0})
        sol2 = Solution(status="OPTIMAL", objective_value=10.001, variables={"x": 10.001})
        warnings = compare_solutions(problem, [sol1, sol2], tolerance=1e-2)
        assert warnings == []
