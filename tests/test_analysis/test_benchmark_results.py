"""
Tests para benchmark_results.py - performance_profile y ResultsExporter.
Usando el patrón existente del proyecto.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pathlib import Path
import tempfile

# Clean mocked modules if they exist (from test_cli/test_benchmark.py)
for mod in ['src.analysis.benchmark_results', 'src.visualization.benchmark_plots']:
    if mod in sys.modules:
        del sys.modules[mod]


class TestPerformanceProfile:
    """Tests para performance_profile."""

    def test_performance_profile_basic(self):
        from src.analysis.benchmark_results import performance_profile
        
        class MockResult:
            def __init__(self, problem_name, solver_name, total_time):
                self.problem_name = problem_name
                self.solver_name = solver_name
                self.total_time = total_time

        results = [
            MockResult("prob1", "solver_a", 1.0),
            MockResult("prob1", "solver_b", 2.0),
            MockResult("prob2", "solver_a", 2.0),
            MockResult("prob2", "solver_b", 4.0),
        ]
        profiles = performance_profile(results)
        
        assert "solver_a" in profiles
        assert "solver_b" in profiles
        assert len(profiles["solver_a"][0]) == 100  # tau values
        assert len(profiles["solver_a"][1]) == 100  # rho values

    def test_performance_profile_single_solver(self):
        from src.analysis.benchmark_results import performance_profile
        
        class MockResult:
            def __init__(self, problem_name, solver_name, total_time):
                self.problem_name = problem_name
                self.solver_name = solver_name
                self.total_time = total_time

        results = [
            MockResult("prob1", "solver_a", 1.0),
            MockResult("prob2", "solver_a", 2.0),
        ]
        profiles = performance_profile(results)
        
        assert "solver_a" in profiles

    def test_performance_profile_custom_tau(self):
        from src.analysis.benchmark_results import performance_profile
        
        class MockResult:
            def __init__(self, problem_name, solver_name, total_time):
                self.problem_name = problem_name
                self.solver_name = solver_name
                self.total_time = total_time

        results = [
            MockResult("prob1", "solver_a", 1.0),
            MockResult("prob1", "solver_b", 1.5),
        ]
        profiles = performance_profile(results, tau_max=5.0, num_points=50)
        
        assert len(profiles["solver_a"][0]) == 50


class TestResultsExporter:
    """Tests para ResultsExporter."""

    def _create_mock_runner(self):
        from src.solver.benchmark import BenchmarkRunner
        from src.core import Solution

        class MockStats:
            def __init__(self):
                self.solve_time = 0.1
                self.build_time = 0.01
                self.iterations = 10
                self.nodes = 0
                self.simplex_iterations = 0
                self.barrier_iterations = 0
                self.crossover_iterations = 0
                self.memory_used_mb = 1.0

        class MockResult:
            def __init__(self, solver, problem, status, obj, time_ms):
                self.solver_name = solver
                self.problem_name = problem
                self.problem_text = "test"
                self.solution = Solution(status=status, objective_value=obj, variables={})
                self.stats = MockStats()
                self.parse_time = 0.01
                self.build_time = 0.01
                self.solve_time = time_ms / 1000
                self.total_time = time_ms / 1000
                self.memory_used_mb = 1.0
                self.peak_memory_mb = 2.0
                self.error = None

        runner = BenchmarkRunner()
        runner.results = [
            MockResult("gurobi", "prob1", "OPTIMAL", 42.0, 100.0),
            MockResult("highs", "prob1", "OPTIMAL", 42.0, 150.0),
        ]
        return runner

    def test_to_markdown(self):
        from src.analysis.benchmark_results import ResultsExporter
        
        runner = self._create_mock_runner()
        exporter = ResultsExporter(runner)
        
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            tmp_path = Path(f.name)
        
        try:
            exporter.to_markdown(tmp_path)
            content = tmp_path.read_text(encoding="utf-8")
            assert "# Reporte de Benchmarking" in content
            assert "gurobi" in content
            assert "highs" in content
        finally:
            os.unlink(tmp_path)

    def test_to_html(self):
        from src.analysis.benchmark_results import ResultsExporter
        
        runner = self._create_mock_runner()
        exporter = ResultsExporter(runner)
        
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            tmp_path = Path(f.name)
        
        try:
            exporter.to_html(tmp_path, include_plots=False)
            content = tmp_path.read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in content
            assert "gurobi" in content
        finally:
            os.unlink(tmp_path)

    def test_to_polars_dataframe(self):
        from src.analysis.benchmark_results import ResultsExporter
        
        runner = self._create_mock_runner()
        exporter = ResultsExporter(runner)
        
        df = exporter.to_polars_dataframe()
        assert len(df) == 2
        assert "problem" in df.columns
        assert "solver" in df.columns

    def test_to_polars_dataframe_with_error(self):
        from src.analysis.benchmark_results import ResultsExporter
        from src.solver.benchmark import BenchmarkRunner
        from src.core import Solution

        class MockStats:
            def __init__(self):
                self.solve_time = 0.1
                self.build_time = 0.01
                self.iterations = 10
                self.nodes = 0
                self.simplex_iterations = 0
                self.barrier_iterations = 0
                self.crossover_iterations = 0
                self.memory_used_mb = 1.0

        class MockResult:
            def __init__(self, solver, problem, status, obj, time_ms, error=None):
                self.solver_name = solver
                self.problem_name = problem
                self.problem_text = "test"
                self.solution = Solution(status=status, objective_value=obj, variables={})
                self.stats = MockStats()
                self.parse_time = 0.01
                self.build_time = 0.01
                self.solve_time = time_ms / 1000
                self.total_time = time_ms / 1000
                self.memory_used_mb = 1.0
                self.peak_memory_mb = 2.0
                self.error = error

        runner = BenchmarkRunner()
        runner.results = [
            MockResult("gurobi", "prob1", "OPTIMAL", 42.0, 100.0, error=None),
            MockResult("highs", "prob2", "ERROR", None, 150.0, error="solver failed"),
        ]
        
        exporter = ResultsExporter(runner)
        df = exporter.to_polars_dataframe()
        assert len(df) == 2

    def test_to_html_with_plots(self):
        import tempfile
        from pathlib import Path
        from src.analysis.benchmark_results import ResultsExporter
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="gurobi",
                problem_name="prob1",
                problem_text="test",
                solution=Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                stats=SolverStats(),
            ),
        ]
        
        exporter = ResultsExporter(runner)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            plots_dir = Path(tmpdir)
            html_path = Path(tmpdir) / "benchmark_report.html"
            exporter.to_html(html_path, include_plots=True, plots_dir=plots_dir)
            
            content = html_path.read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in content
            assert "benchmark_times.png" in content

    def test_export_benchmark_results(self):
        from pathlib import Path
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats
        from src.analysis.benchmark_results import export_benchmark_results

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="test_solver",
                problem_name="prob1",
                problem_text="test",
                solution=Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                stats=SolverStats(),
            ),
        ]
        
        imports_ok = True
        try:
            import src.visualization.benchmark_plots as bp
            imports_ok = True
        except ImportError:
            imports_ok = False
        
        if imports_ok:
            import tempfile
            from pathlib import Path
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                paths = export_benchmark_results(runner, output_dir, formats=["json"], include_plots=False)
                assert "json" in paths
                assert os.path.exists(paths["json"])
        else:
            import tempfile
            from pathlib import Path
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                paths = export_benchmark_results(runner, output_dir, formats=["json"], include_plots=False)
                assert "json" in paths
                assert os.path.exists(paths["json"])

    def test_export_benchmark_results_md(self):
        from pathlib import Path
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats
        from src.analysis.benchmark_results import export_benchmark_results

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="test_solver",
                problem_name="prob1",
                problem_text="test",
                solution=Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                stats=SolverStats(),
            ),
        ]
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            paths = export_benchmark_results(runner, output_dir, formats=["md"], include_plots=False)
            assert "md" in paths
            assert os.path.exists(paths["md"])

    def test_export_benchmark_results_csv(self):
        from pathlib import Path
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats
        from src.analysis.benchmark_results import export_benchmark_results

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="test_solver",
                problem_name="prob1",
                problem_text="test",
                solution=Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                stats=SolverStats(),
            ),
        ]
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            paths = export_benchmark_results(runner, output_dir, formats=["csv"], include_plots=False)
            assert "csv" in paths
            assert os.path.exists(paths["csv"])

    def test_export_benchmark_results_all_formats(self):
        from pathlib import Path
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats
        from src.analysis.benchmark_results import export_benchmark_results

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="test_solver",
                problem_name="prob1",
                problem_text="test",
                solution=Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                stats=SolverStats(),
            ),
        ]
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            paths = export_benchmark_results(runner, output_dir, formats=["json", "md", "csv"], include_plots=False)
            assert "json" in paths
            assert "md" in paths
            assert "csv" in paths

    def test_export_benchmark_results_html(self):
        from pathlib import Path
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats
        from src.analysis.benchmark_results import export_benchmark_results

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="test_solver",
                problem_name="prob1",
                problem_text="test",
                solution=Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                stats=SolverStats(),
            ),
        ]
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            paths = export_benchmark_results(runner, output_dir, formats=["html"], include_plots=False)
            assert "html" in paths
            assert os.path.exists(paths["html"])
            content = paths["html"].read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in content