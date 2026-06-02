"""
Tests para multi_analysis.py - MultiLPAnalysis.
Usando el patrón existente del proyecto.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import tempfile

from src.core import LinearConstraint, LinearProblem, Solution, VariableBound
from src.solver.multi_solver import MultiSolverResult, ProblemResult


class TestMultiLPAnalysis:
    """Tests para MultiLPAnalysis."""

    def _create_multi_result(self, num_results=2, with_error=False, with_feasible_region=False):
        results = []
        for i in range(num_results):
            if with_feasible_region:
                problem = LinearProblem(
                    objective={"x": 1, "y": 1},
                    sense="max",
                    constraints=[
                        LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<="),
                        LinearConstraint(coefficients={"x": 1, "y": 0}, rhs=5, sense="<="),
                    ],
                    variables=["x", "y"],
                    bounds={
                        "x": VariableBound(variable="x", lower=0),
                        "y": VariableBound(variable="y", lower=0),
                    },
                    name=f"Problem {i+1}",
                )
                solution = Solution(
                    status="OPTIMAL",
                    objective_value=10.0 * (i + 1),
                    variables={"x": float(i + 1), "y": 0.0},
                )
            else:
                problem = LinearProblem(
                    objective={"x": 1},
                    sense="max",
                    constraints=[],
                    variables=["x"],
                    bounds={},
                    name=f"Problem {i+1}",
                )
                solution = Solution(
                    status="OPTIMAL",
                    objective_value=42.0 * (i + 1),
                    variables={"x": float(i + 1)},
                )

            if with_error and i == 0:
                result = ProblemResult(
                    problem=problem,
                    solution=Solution(status="ERROR", objective_value=None, variables={}),
                    error="Solver error",
                )
            else:
                result = ProblemResult(
                    problem=problem,
                    solution=solution,
                )
            results.append(result)

        multi_result = MultiSolverResult()
        multi_result.results = results
        return multi_result

    def test_generate_pdf_basic(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        multi_result = self._create_multi_result(num_results=1)
        analysis = MultiLPAnalysis(multi_result)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_multiple_problems(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        multi_result = self._create_multi_result(num_results=3)
        analysis = MultiLPAnalysis(multi_result)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_error_result(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        multi_result = self._create_multi_result(num_results=2, with_error=True)
        analysis = MultiLPAnalysis(multi_result)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_pdf_with_feasible_region(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        multi_result = self._create_multi_result(num_results=1, with_feasible_region=True)
        analysis = MultiLPAnalysis(multi_result)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            analysis.generate_pdf(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_page_count(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        multi_result = self._create_multi_result(num_results=2)
        analysis = MultiLPAnalysis(multi_result)
        assert analysis.page_count == 0

    def test_build_portada(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        multi_result = self._create_multi_result(num_results=2)
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_portada(pdf)

    def test_build_resumen(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        multi_result = self._create_multi_result(num_results=2)
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_resumen(pdf)

    def test_build_tabla_resultados(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        multi_result = self._create_multi_result(num_results=2)
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_tabla_resultados(pdf)

    def test_build_interpretacion(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        multi_result = self._create_multi_result(num_results=2)
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_interpretacion(pdf)

    def test_build_estadisticas(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        multi_result = self._create_multi_result(num_results=2)
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_estadisticas_resumen(pdf)

    def test_build_solucion(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})
        result = ProblemResult(problem=problem, solution=solution)

        multi_result = MultiSolverResult()
        multi_result.results = [result]
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_solucion(pdf, result)

    def test_build_sensibilidad(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti
        from src.analysis.sensitivity import SensitivityAnalysis, SensitivityRange

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})
        solution.sensitivity = SensitivityAnalysis(
            objective_ranges=[SensitivityRange(name="x", current=1.0, lower=0.5, upper=2.0)],
            rhs_ranges=[],
            bound_ranges=[],
        )
        result = ProblemResult(problem=problem, solution=solution)

        multi_result = MultiSolverResult()
        multi_result.results = [result]
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_sensibilidad(pdf, result)

    def test_build_holguras(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=")],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})
        result = ProblemResult(problem=problem, solution=solution)

        multi_result = MultiSolverResult()
        multi_result.results = [result]
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_holguras(pdf, result)

    def test_build_tiempos_problema(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})
        result = ProblemResult(problem=problem, solution=solution, parse_time=0.1, build_time=0.2, solve_time=0.3, total_time=0.6)

        multi_result = MultiSolverResult()
        multi_result.results = [result]
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_tiempos_problema(pdf, result)

    def test_build_tiempos_resumen(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        multi_result = self._create_multi_result(num_results=2)
        multi_result.total_parse_time = 0.1
        multi_result.total_build_time = 0.2
        multi_result.total_solve_time = 0.3
        multi_result.total_time = 0.6
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_tiempos_resumen(pdf)

    def test_calcular_holguras(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        problem = LinearProblem(
            objective={"x": 1, "y": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<=")],
            variables=["x", "y"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 5, "y": 5})
        result = ProblemResult(problem=problem, solution=solution)

        analysis = MultiLPAnalysis(MultiSolverResult())
        holguras = analysis._calcular_holguras(result)

        # Slack = rhs - sum(coeff * var_value) = 10 - (1*5 + 1*5) = 0
        assert 0 in holguras

    def test_format_tiempo(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        analysis = MultiLPAnalysis(MultiSolverResult())

        # Less than 1 second
        assert analysis._format_tiempo(0.5) == "500.00 ms"
        # Very small time still formats
        result = analysis._format_tiempo(0.001)
        assert "ms" in result

        # Greater or equal to 1 second
        assert analysis._format_tiempo(1.5) == "1.500 s"
        assert analysis._format_tiempo(2.0) == "2.000 s"

    def test_format_objective(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        analysis = MultiLPAnalysis(MultiSolverResult())

        # Positive coefficients
        obj1 = {"x": 1, "y": 2}
        result = analysis._format_objective(obj1)
        assert "x" in result and "y" in result

    def test_format_constraint(self):
        from src.analysis.multi_analysis import MultiLPAnalysis

        analysis = MultiLPAnalysis(MultiSolverResult())

        c = LinearConstraint(coefficients={"x": 1, "y": 2}, rhs=10, sense="<=")
        result = analysis._format_constraint(c)
        assert "x" in result and "y" in result

    def test_build_error_problema(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=None, variables={})
        result = ProblemResult(problem=problem, solution=solution, error="Solver failed")

        multi_result = MultiSolverResult()
        multi_result.results = [result]
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_error_problema(pdf, result)

    def test_build_funcion_objetivo_minimization(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        problem = LinearProblem(
            objective={"x": 1},
            sense="min",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})
        result = ProblemResult(problem=problem, solution=solution)

        multi_result = MultiSolverResult()
        multi_result.results = [result]
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_funcion_objetivo(pdf, result)

    def test_build_restricciones(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=")],
            variables=["x"],
            bounds={},
        )
        solution = Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 10})
        result = ProblemResult(problem=problem, solution=solution)

        multi_result = MultiSolverResult()
        multi_result.results = [result]
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        analysis._build_restricciones(pdf, result)

    def test_build_grafico_no_matplotlib(self):
        from src.analysis.multi_analysis import MultiLPAnalysis, ReporteAcademicoMulti

        problem = LinearProblem(
            objective={"x": 1, "y": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<=")],
            variables=["x", "y"],
            bounds={
                "x": VariableBound(variable="x", lower=0),
                "y": VariableBound(variable="y", lower=0),
            },
        )
        solution = Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 5, "y": 0})
        result = ProblemResult(problem=problem, solution=solution)

        multi_result = MultiSolverResult()
        multi_result.results = [result]
        analysis = MultiLPAnalysis(multi_result)

        pdf = ReporteAcademicoMulti()
        pdf.set_margins(20, 20, 20)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # This will handle ImportError gracefully
        analysis._build_grafico(pdf, result)
