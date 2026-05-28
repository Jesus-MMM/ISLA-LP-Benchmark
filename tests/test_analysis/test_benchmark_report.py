"""
Tests para benchmark_report.py - BenchmarkReport y BenchmarkPDF.
Usando el patrón existente del proyecto.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import tempfile


class TestBenchmarkPDF:
    """Tests para BenchmarkPDF."""

    def test_header_and_footer(self):
        from src.analysis.benchmark_report import BenchmarkPDF
        
        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.add_page()
        
        # Test header does nothing (no exception)
        pdf.header()
        
        # Test footer - set text and verify no exception
        pdf.footer()
        
        # Page count may have increased due to auto footer behavior
        assert pdf.page_no() >= 1


class TestBenchmarkReport:
    """Tests para BenchmarkReport."""

    def _create_mock_runner(self, results=None):
        from src.solver.benchmark import BenchmarkRunner
        from src.core import Solution

        class MockStats:
            def __init__(self):
                self.iterations = 10
                self.nodes = 5
                self.solve_time = 0.1
                self.build_time = 0.01
                self.memory_used_mb = 1.0
                self.peak_memory_mb = 2.0

        class MockResult:
            def __init__(self, solver, problem, status, obj, time_val=1.0):
                self.solver_name = solver
                self.problem_name = problem
                self.problem_text = "max: x <= 10;"
                self.solution = Solution(status=status, objective_value=obj, variables={})
                self.stats = MockStats()
                self.total_time = time_val
                self.memory_used_mb = 1.0
                self.peak_memory_mb = 2.0
                self.error = None

        runner = BenchmarkRunner()
        if results is None:
            runner.results = [
                MockResult("gurobi", "prob1", "OPTIMAL", 42.0),
                MockResult("highs", "prob1", "OPTIMAL", 42.0),
            ]
        else:
            runner.results = results
        return runner

    def test_generate_basic_report(self):
        from src.analysis.benchmark_report import BenchmarkReport

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            report.generate(tmp_path)
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0
        finally:
            os.unlink(tmp_path)

    def test_generate_with_system_info(self):
        from src.analysis.benchmark_report import BenchmarkReport

        runner = self._create_mock_runner()
        system_info = {
            "platform": {
                "system": "Windows",
                "release": "10",
                "machine": "AMD64",
                "processor": "Intel",
                "python_version": "3.12.0",
            },
            "hostname": "test-host",
            "timestamp": "2026-01-01T12:00:00",
        }
        report = BenchmarkReport(runner, system_info=system_info)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            report.generate(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_has_charts_true(self):
        from src.analysis.benchmark_report import BenchmarkReport

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)
        
        assert report._has_charts() is True

    def test_has_charts_false(self):
        from src.analysis.benchmark_report import BenchmarkReport

        runner = self._create_mock_runner(results=[])
        report = BenchmarkReport(runner)
        
        assert report._has_charts() is False

    def test_cover_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._cover(pdf)
        # Verify no exception raised

    def test_summary_stats_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._summary_stats(pdf)

    def test_solver_comparison_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._solver_comparison(pdf)

    def test_detailed_results_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._detailed_results(pdf)

    def test_problem_definitions_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._problem_definitions(pdf)

    def test_scalability_analysis_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._scalability_analysis(pdf)

    def test_correlation_matrix_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._correlation_matrix(pdf)

    def test_outliers_detection_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._outliers_detection(pdf)

    def test_statistical_analysis_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        # Need at least 2 solvers and 2 problems for statistical analysis
        class MockStats:
            def __init__(self):
                self.iterations = 10
                self.nodes = 5

        class MockResult:
            def __init__(self, solver, problem, status, obj, time_val=1.0):
                self.solver_name = solver
                self.problem_name = problem
                self.problem_text = "max: x <= 10;"
                self.solution = Solution(status=status, objective_value=obj, variables={})
                self.stats = MockStats()
                self.total_time = time_val

        from src.solver.benchmark import BenchmarkRunner
        from src.core import Solution

        runner = BenchmarkRunner()
        runner.results = [
            MockResult("gurobi", "prob1", "OPTIMAL", 42.0),
            MockResult("highs", "prob1", "OPTIMAL", 43.0),
            MockResult("gurobi", "prob2", "OPTIMAL", 50.0),
            MockResult("highs", "prob2", "OPTIMAL", 51.0),
        ]
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._statistical_analysis(pdf)

    def test_recommendations_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._recommendations(pdf)

    def test_memory_analysis_page(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._memory_analysis(pdf)

    def test_header_method(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.add_page()
        
        report._header(pdf, "TEST TITLE")

    def test_system_page_without_system_info(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner, system_info={})

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._system(pdf)

    def test_generate_with_multiple_solvers_and_problems(self):
        from src.analysis.benchmark_report import BenchmarkReport

        class MockStats:
            def __init__(self):
                self.iterations = 5
                self.nodes = 2

        class MockResult:
            def __init__(self, solver, problem, status, obj, time_val):
                self.solver_name = solver
                self.problem_name = problem
                self.problem_text = "max: x <= 10;"
                self.solution = Solution(status=status, objective_value=obj, variables={})
                self.stats = MockStats()
                self.total_time = time_val
                self.memory_used_mb = 1.0
                self.peak_memory_mb = 2.0
                self.error = None

        from src.solver.benchmark import BenchmarkRunner
        from src.core import Solution

        runner = BenchmarkRunner()
        runner.results = [
            MockResult("gurobi", "prob1", "OPTIMAL", 42.0, 0.1),
            MockResult("highs", "prob1", "OPTIMAL", 42.0, 0.2),
            MockResult("gurobi", "prob2", "OPTIMAL", 50.0, 0.15),
            MockResult("highs", "prob2", "OPTIMAL", 50.0, 0.25),
        ]

        report = BenchmarkReport(runner)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            report.generate(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generation_without_charts_no_matplotlib(self):
        from src.analysis.benchmark_report import BenchmarkReport

        runner = self._create_mock_runner(results=[])
        report = BenchmarkReport(runner)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name

        try:
            report.generate(tmp_path)
            assert os.path.exists(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_generate_time_chart(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._generate_time_chart(pdf)

    def test_generate_success_chart(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._generate_success_chart(pdf)

    def test_generate_memory_chart(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._generate_memory_chart(pdf)

    def test_performance_profiles_chart(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner()
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._performance_profiles(pdf)

    def test_performance_profiles_no_data(self):
        from src.analysis.benchmark_report import BenchmarkReport, BenchmarkPDF

        runner = self._create_mock_runner(results=[])
        report = BenchmarkReport(runner)

        pdf = BenchmarkPDF()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        report._performance_profiles(pdf)