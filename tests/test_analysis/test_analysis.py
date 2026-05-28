"""
Tests para LPAnalysis y ReporteAcademico.
Usando el patrón existente del proyecto.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import tempfile


class TestExecutionTimes:
    """Tests para ExecutionTimes."""

    def test_default_values(self):
        from src.analysis.analysis import ExecutionTimes

        times = ExecutionTimes()
        assert times.parse_time == 0.0
        assert times.build_time == 0.0
        assert times.solve_time == 0.0
        assert times.total_time == 0.0

    def test_custom_values(self):
        from src.analysis.analysis import ExecutionTimes

        times = ExecutionTimes(
            parse_time=0.1,
            solve_time=0.5,
            total_time=1.0,
        )
        assert times.parse_time == 0.1
        assert times.solve_time == 0.5
        assert times.total_time == 1.0


class TestLPAnalysisInit:
    """Tests para LPAnalysis inicializacion."""

    def test_init_minimal(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})

        analysis = LPAnalysis(problem, solution)
        assert analysis.problem is problem
        assert analysis.solution.status == "OPTIMAL"

    def test_init_with_times(self):
        from src.analysis.analysis import LPAnalysis, ExecutionTimes
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})
        times = ExecutionTimes(parse_time=0.1, solve_time=0.2)

        analysis = LPAnalysis(problem, solution, times=times)
        assert analysis.times.parse_time == 0.1
        assert analysis.times.solve_time == 0.2


class TestLPAnalysisPDFGeneration:
    """Tests para generacion de PDF."""

    def test_generate_pdf_creates_file(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10, "y": 0})

        analysis = LPAnalysis(problem, solution, solver_name="test_solver")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_single_variable(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_constraints(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, LinearConstraint, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=")],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_non_optimal_status(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="INFEASIBLE", objective_value=None, variables={})

        analysis = LPAnalysis(problem, solution, solver_name="test_solver")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_iterations_and_nodes(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(
            status="OPTIMAL",
            objective_value=42.0,
            variables={"x": 10, "y": 0},
            iterations=100,
            nodes=50,
        )

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_reduced_costs(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(
            status="OPTIMAL",
            objective_value=42.0,
            variables={"x": 10, "y": 0},
            reduced_costs={"x": 0, "y": 1.5},
        )

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_dual_values(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, LinearConstraint, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<="),
                LinearConstraint(coefficients={"x": 0, "y": 1}, rhs=5, sense=">="),
            ],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(
            status="OPTIMAL",
            objective_value=42.0,
            variables={"x": 10, "y": 0},
            dual_values={"c1": 0.5, "c2": 0.0},
        )

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_sensitivity(self):
        from src.analysis.analysis import LPAnalysis
        from src.analysis.sensitivity import SensitivityAnalysis, SensitivityRange
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10, "y": 0})

        sens = SensitivityAnalysis(
            objective_ranges=[
                SensitivityRange(name="x", current=1.0, lower=0.5, upper=2.0, reduced_cost=0.0),
            ],
            rhs_ranges=[
                SensitivityRange(name="c1", current=10.0, lower=5.0, upper=15.0, dual_value=0.5),
            ],
            bound_ranges=[],
        )

        analysis = LPAnalysis(problem, solution, sensitivity=sens)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_system_info(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10, "y": 0})

        system_info = {
            "platform": {
                "python_version": "3.12.0",
                "system": "Windows",
                "release": "10",
                "processor": "Intel",
                "machine": "AMD64",
            },
            "hostname": "test-host",
            "timestamp": "2026-01-01T12:00:00",
        }

        analysis = LPAnalysis(problem, solution, system_info=system_info)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_times_all_positive(self):
        from src.analysis.analysis import LPAnalysis, ExecutionTimes
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})
        times = ExecutionTimes(parse_time=0.1, build_time=0.2, solve_time=0.3, visualize_time=0.4, pdf_time=0.5, total_time=1.5)

        analysis = LPAnalysis(problem, solution, times=times)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_bounds(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution, VariableBound

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0, upper=100), "y": VariableBound(variable="y", lower=0)},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10, "y": 0})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_numerical_quality(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution, NumericalQuality

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(
            status="OPTIMAL",
            objective_value=42.0,
            variables={"x": 10, "y": 0},
            numerical_quality=NumericalQuality(
                max_bound_viol=1e-9,
                max_constraint_viol=1e-8,
                condition_number=123.45,
            ),
        )

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_progress_log(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution, ProgressPoint

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(
            status="OPTIMAL",
            objective_value=42.0,
            variables={"x": 10, "y": 0},
            progress_log=[
                ProgressPoint(iteration=1, time=0.1, objective=50.0, gap=0.1, nodes=10),
                ProgressPoint(iteration=2, time=0.2, objective=45.0, gap=0.05, nodes=20),
            ],
        )

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_minimization_problem(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="min",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10, "y": 0})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_graphic_with_feasible_region(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, LinearConstraint, Solution, VariableBound

        problem = LinearProblem(
            objective={"x": 2, "y": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<="),
                LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="<="),
            ],
            variables=["x", "y"],
            bounds={"x": VariableBound(variable="x", lower=0), "y": VariableBound(variable="y", lower=0)},
        )
        solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 5, "y": 0})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_sensitivity_ranges_with_none_values(self):
        from src.analysis.analysis import LPAnalysis
        from src.analysis.sensitivity import SensitivityAnalysis, SensitivityRange
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10, "y": 0})

        sens = SensitivityAnalysis(
            objective_ranges=[
                SensitivityRange(name="x", current=1.0, lower=None, upper=None, reduced_cost=None),
            ],
            rhs_ranges=[
                SensitivityRange(name="c1", current=10.0, lower=5.0, upper=15.0, dual_value=0.5),
            ],
            bound_ranges=[
                SensitivityRange(name="y", current=0.0, lower=0.0, upper=100.0),
            ],
        )

        analysis = LPAnalysis(problem, solution, sensitivity=sens)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_long_constraint(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, LinearConstraint, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(
                    coefficients={"x": 1, "y": 2, "z": 3, "w": 4},
                    rhs=100,
                    sense="<="
                )
            ],
            variables=["x", "y", "z", "w"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10, "y": 0, "z": 0, "w": 0})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_equality_constraint(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, LinearConstraint, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="="),
            ],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 5, "y": 5})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_geq_constraint(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, LinearConstraint, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=5, sense=">="),
            ],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_model_with_errors(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=[],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_model_with_warnings(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_highs_solver(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, Solution

        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10, "y": 0})

        analysis = LPAnalysis(problem, solution, solver_name="highs")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_slack_table_empty_variables(self):
        from src.analysis.analysis import LPAnalysis
        from src.core import LinearProblem, LinearConstraint, Solution

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<="),
            ],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={})

        analysis = LPAnalysis(problem, solution)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)