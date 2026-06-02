"""
Tests for Solution and SolutionTable.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.solution import NumericalQuality, ProgressPoint, Solution


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

    def test_is_infeasible(self):
        """Test is_infeasible method."""
        sol = Solution(status="INFEASIBLE", objective_value=None, variables={})
        assert sol.is_infeasible()

        sol2 = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 1.0})
        assert not sol2.is_infeasible()

    def test_is_unbounded(self):
        """Test is_unbounded method."""
        sol = Solution(status="UNBOUNDED", objective_value=None, variables={})
        assert sol.is_unbounded()

        sol2 = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 1.0})
        assert not sol2.is_unbounded()

    def test_has_errors(self):
        """Test has_errors method."""
        sol = Solution(status="ERROR: solver crashed", objective_value=None, variables={})
        assert sol.has_errors()

        sol2 = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 1.0})
        assert not sol2.has_errors()

        sol3 = Solution(status="ERROR_OUT_OF_MEMORY", objective_value=None, variables={})
        assert sol3.has_errors()

    def test_print_summary_non_verbose(self):
        """Test print_summary with verbose=False."""
        sol = Solution(
            status="OPTIMAL",
            objective_value=10.5,
            variables={"x": 2.0, "y": 3.0},
        )
        summary = sol.print_summary(verbose=False)
        assert "OPTIMAL" in summary
        assert "10.5" in summary
        assert "x = 2.0" in summary or "x = 2.0000" in summary

    def test_print_summary_verbose(self):
        """Test print_summary with verbose=True."""
        sol = Solution(
            status="OPTIMAL",
            objective_value=10.5,
            variables={"x": 2.0},
            dual_values={"c1": 0.5},
            reduced_costs={"x": 0.0},
            iterations=100,
            nodes=5,
        )
        summary = sol.print_summary(verbose=True)
        assert "Costos reducidos" in summary
        assert "Precios sombra" in summary
        assert "Iteraciones" in summary
        assert "100" in summary
        assert "Nodos" in summary
        assert "5" in summary

    def test_print_summary_verbose_no_duals(self):
        """Test print_summary verbose without dual values."""
        sol = Solution(
            status="OPTIMAL",
            objective_value=10.0,
            variables={"x": 1.0},
        )
        summary = sol.print_summary(verbose=True)
        assert "Estado: OPTIMAL" in summary

    def test_str_optimal(self):
        """Test __str__ for optimal solution."""
        sol = Solution(
            status="OPTIMAL",
            objective_value=10.5,
            variables={"x": 2.0, "y": 3.0},
        )
        s = str(sol)
        assert "OPTIMAL" in s
        assert "Z=" in s or "10.5" in s

    def test_str_infeasible(self):
        """Test __str__ for infeasible solution."""
        sol = Solution(status="INFEASIBLE", objective_value=None, variables={})
        assert str(sol) == "INFEASIBLE"

    def test_str_unbounded(self):
        """Test __str__ for unbounded solution."""
        sol = Solution(status="UNBOUNDED", objective_value=None, variables={})
        assert str(sol) == "UNBOUNDED"

    def test_none_objective_value(self):
        """Test solution with None objective_value."""
        sol = Solution(status="INFEASIBLE", objective_value=None, variables={})
        assert sol.objective_value is None

    def test_empty_variables(self):
        """Test solution with empty variables dictionary."""
        sol = Solution(status="OPTIMAL", objective_value=0.0, variables={})
        assert sol.variables == {}

    def test_progress_point(self):
        """Test ProgressPoint dataclass."""
        pp = ProgressPoint(iteration=1, time=0.5, objective=100.0, gap=0.05, nodes=10)
        assert pp.iteration == 1
        assert pp.time == 0.5
        assert pp.objective == 100.0
        assert pp.gap == 0.05
        assert pp.nodes == 10

    def test_numerical_quality_defaults(self):
        """Test NumericalQuality default values."""
        nq = NumericalQuality()
        assert nq.max_bound_viol == 0.0
        assert nq.max_constraint_viol == 0.0
        assert nq.condition_number is None


class TestSolutionTable:
    """Tests for SolutionTable."""

    def test_to_solution_table(self):
        """Test to_solution_table function."""
        from src.core.constraint import LinearConstraint
        from src.core.problem import LinearProblem
        from src.core.solution import to_solution_table

        problem = LinearProblem(
            objective={"x": 3, "y": 4},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 2}, rhs=10, sense="<="),
            ],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(
            status="OPTIMAL",
            objective_value=26.0,
            variables={"x": 2.0, "y": 4.0},
        )
        table = to_solution_table(solution, problem)
        assert table.objective_terms is not None
        assert table.constraints is not None
        assert table.variables is not None

    def test_to_solution_table_iis(self):
        """Test to_solution_table with IIS."""
        from src.core.problem import LinearProblem
        from src.core.solution import to_solution_table

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(
            status="INFEASIBLE",
            objective_value=None,
            variables={},
            iis=["c1", "c2"],
        )
        table = to_solution_table(solution, problem)
        assert table.iis == ["c1", "c2"]

    def test_to_solution_table_non_lp_problem(self):
        """Test to_solution_table with non-LinearProblem returns empty."""
        from src.core.solution import SolutionTable, to_solution_table

        solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 1.0})
        table = to_solution_table(solution, problem=None)
        assert isinstance(table, SolutionTable)
        assert table.variables is None
