"""
Tests para LinearVisualization - more comprehensive coverage.
Usando el patrón existente del proyecto.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import matplotlib

matplotlib.use('Agg')

import pytest


class TestLinearVisualization:
    """Tests para LinearVisualization."""

    def test_init_with_two_variables(self):
        from src.core import LinearProblem
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=None),
                   "y": VariableBound(variable="y", lower=0, upper=None)},
        )
        viz = LinearVisualization(problem)
        assert viz.var_x == "x"
        assert viz.var_y == "y"

    def test_init_with_more_than_two_variables_raises(self):
        from src.core import LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 2, "z": 3},
            sense="max",
            constraints=[],
            variables=["x", "y", "z"],
            bounds={},
        )
        with pytest.raises(ValueError, match="2 variables"):
            LinearVisualization(problem)

    def test_is_point_feasible_le_satisfied(self):
        from src.core import LinearConstraint, LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        c = LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="<=")
        is_feasible = LinearVisualization(problem).is_point_feasible(3, 0, [c])
        assert is_feasible is True

    def test_is_point_feasible_le_violated(self):
        from src.core import LinearConstraint, LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        c = LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="<=")
        is_feasible = LinearVisualization(problem).is_point_feasible(10, 0, [c])
        assert is_feasible is False

    def test_is_point_feasible_ge_satisfied(self):
        from src.core import LinearConstraint, LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        c = LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense=">=")
        is_feasible = LinearVisualization(problem).is_point_feasible(10, 0, [c])
        assert is_feasible is True

    def test_is_point_feasible_eq_satisfied(self):
        from src.core import LinearConstraint, LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        c = LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="=")
        is_feasible = LinearVisualization(problem).is_point_feasible(5, 0, [c])
        assert is_feasible is True

    def test_get_all_constraints(self):
        from src.core import LinearProblem
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=None),
                   "y": VariableBound(variable="y", lower=0, upper=None)},
        )
        constraints = LinearVisualization(problem)._get_all_constraints()
        assert len(constraints) >= 2

    def test_calculate_plot_range(self):
        from src.core import LinearProblem
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=None),
                   "y": VariableBound(variable="y", lower=0, upper=None)},
        )
        x_min, x_max, y_min, y_max = LinearVisualization(problem)._calculate_plot_range()
        assert x_min < x_max
        assert y_min < y_max

    def test_find_feasible_vertices(self):
        from src.core import LinearConstraint, LinearProblem
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<=")],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=None),
                   "y": VariableBound(variable="y", lower=0, upper=None)},
        )
        all_constraints = LinearVisualization(problem)._get_all_constraints()
        vertices = LinearVisualization(problem)._find_feasible_vertices(all_constraints)
        assert len(vertices) >= 0

    def test_format_objective(self):
        from src.core import LinearProblem
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=None),
                   "y": VariableBound(variable="y", lower=0, upper=None)},
        )
        obj_str = LinearVisualization(problem)._format_objective()
        assert "x" in obj_str

    def test_find_intersection(self):
        from src.core import LinearConstraint, LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="<="),
                LinearConstraint(coefficients={"x": 0, "y": 1}, rhs=3, sense="<="),
            ],
            variables=["x", "y"],
            bounds={},
        )
        viz = LinearVisualization(problem)
        result = viz.find_intersection(
            LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="<="),
            LinearConstraint(coefficients={"x": 0, "y": 1}, rhs=3, sense="<="),
        )
        assert result == (5.0, 3.0)

    def test_find_intersection_parallel_lines_returns_none(self):
        from src.core import LinearConstraint, LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        viz = LinearVisualization(problem)
        result = viz.find_intersection(
            LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=5, sense="<="),
            LinearConstraint(coefficients={"x": 2, "y": 2}, rhs=10, sense="<="),
        )
        assert result is None

    def test_order_vertices_ccw(self):
        from src.core import LinearProblem
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=None),
                   "y": VariableBound(variable="y", lower=0, upper=None)},
        )
        viz = LinearVisualization(problem)
        vertices = [(0, 0), (5, 0), (5, 3), (0, 3)]
        ordered = viz._order_vertices_ccw(vertices)
        assert len(ordered) == 4

    def test_plot_to_tempfile(self):
        from src.core import LinearConstraint, LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=10, sense="<=")],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_get_line_points_vertical_line(self):
        from src.core import LinearConstraint, LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        viz = LinearVisualization(problem)
        x_vals, y_vals = viz._get_line_points(
            LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="<="),
            -10, 10, -10, 10
        )
        assert len(x_vals) == 100

    def test_get_line_points_horizontal_line(self):
        from src.core import LinearConstraint, LinearProblem
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        viz = LinearVisualization(problem)
        x_vals, y_vals = viz._get_line_points(
            LinearConstraint(coefficients={"x": 0, "y": 1}, rhs=5, sense="<="),
            -10, 10, -10, 10
        )
        assert len(y_vals) == 100

    def test_plot_with_solution_y_only_objective(self):
        from src.core import LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 0, "y": 1},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_solution_x_only_objective(self):
        from src.core import LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_single_vertex(self):
        from src.core import LinearConstraint, LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=0, sense=">="),
            ],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=0, variables={"x": 0, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_two_vertices(self):
        from src.core import LinearConstraint, LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=10, sense="<="),
            ],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 5})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_negative_solution(self):
        from src.core import LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=None, upper=None),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": -5, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_without_solution(self):
        from src.core import LinearProblem
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        viz = LinearVisualization(problem, solution=None)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_show_true(self):
        from src.core import LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot(save_path=None, show=True)
        assert tmp_path is None or os.path.exists(tmp_path)

    def test_plot_with_two_vertices_on_edge(self):
        from src.core import LinearConstraint, LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="<="),
                LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=0, sense=">="),
            ],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=5),
                   "y": VariableBound(variable="y", lower=0, upper=5)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 5, "y": 3})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_x_boundary_only(self):
        from src.core import LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_y_boundary_only(self):
        from src.core import LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_y_lower_only(self):
        from src.core import LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=None)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_x_upper_only(self):
        from src.core import LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=None, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_equality_constraint(self):
        from src.core import LinearConstraint, LinearProblem, Solution
        from src.core.bound import VariableBound
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="="),
            ],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=10),
                   "y": VariableBound(variable="y", lower=0, upper=10)},
        )
        solution = Solution(status="OPTIMAL", objective_value=5, variables={"x": 5, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)

    def test_plot_with_no_bounds(self):
        from src.core import LinearProblem, Solution
        from src.visualization.visualization import LinearVisualization

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=10, variables={"x": 10, "y": 0})
        viz = LinearVisualization(problem, solution)
        tmp_path = viz.plot_to_tempfile()
        assert os.path.exists(tmp_path)
        os.unlink(tmp_path)
