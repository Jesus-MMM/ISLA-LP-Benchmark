"""
Tests para MultiSolver y MultiSolverResult.
Usando el patrón existente del proyecto.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest


class TestProblemResult:
    """Tests para ProblemResult."""

    def test_init_default_values(self):
        from src.core import LinearProblem, Solution
        from src.solver.multi_solver import ProblemResult

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        result = ProblemResult(problem=problem, solution=Solution(status="OK", objective_value=None, variables={}))

        assert result.parse_time == 0.0
        assert result.build_time == 0.0
        assert result.total_time == 0.0
        assert result.error is None

    def test_init_custom_values(self):
        from src.core import LinearProblem, Solution
        from src.solver.multi_solver import ProblemResult

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 1})
        result = ProblemResult(
            problem=problem,
            solution=solution,
            parse_time=0.1,
            solve_time=0.2,
            error="some error",
        )

        assert result.parse_time == 0.1
        assert result.solve_time == 0.2
        assert result.error == "some error"


class TestMultiSolverResult:
    """Tests para MultiSolverResult."""

    def test_init_default_values(self):
        from src.solver.multi_solver import MultiSolverResult

        result = MultiSolverResult()
        assert len(result.results) == 0
        assert result.total_time == 0.0

    def test_get_successful_results(self):
        from src.core import LinearProblem, Solution
        from src.solver.multi_solver import MultiSolverResult, ProblemResult

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )

        result = MultiSolverResult()
        result.results = [
            ProblemResult(problem=problem, solution=Solution(status="OPTIMAL", objective_value=42.0, variables={}), error=None),
            ProblemResult(problem=problem, solution=Solution(status="ERROR", objective_value=None, variables={}), error="failed"),
        ]

        successful = result.get_successful_results()
        assert len(successful) == 1

    def test_get_failed_results(self):
        from src.core import LinearProblem, Solution
        from src.solver.multi_solver import MultiSolverResult, ProblemResult

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )

        result = MultiSolverResult()
        result.results = [
            ProblemResult(problem=problem, solution=Solution(status="OPTIMAL", objective_value=42.0, variables={}), error=None),
            ProblemResult(problem=problem, solution=Solution(status="ERROR", objective_value=None, variables={}), error="failed"),
        ]

        failed = result.get_failed_results()
        assert len(failed) == 1


class TestMultiSolver:
    """Tests para MultiSolver."""

    def test_init_gurobi(self):
        from src.solver.multi_solver import MultiSolver

        solver = MultiSolver(solver_name="gurobi", verbose=False)
        assert solver.solver_name == "gurobi"
        assert solver.verbose is False

    def test_init_unknown_solver_raises(self):
        from src.solver.multi_solver import MultiSolver

        with pytest.raises(ValueError, match="no encontrado"):
            MultiSolver(solver_name="nonexistent_solver")

    def test_solve_all_empty_list(self):
        from src.solver.multi_solver import MultiSolver

        solver = MultiSolver(solver_name="gurobi", verbose=False)
        result = solver.solve_all([])
        assert len(result.results) == 0
        assert result.solver_name == "gurobi"

    def test_solve_from_text_empty(self):
        from src.solver.multi_solver import MultiSolver, MultiSolverResult

        result = MultiSolver.solve_from_text("", solver_name="gurobi")
        assert isinstance(result, MultiSolverResult)
        assert len(result.results) == 0
