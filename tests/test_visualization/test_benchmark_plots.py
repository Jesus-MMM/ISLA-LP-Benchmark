"""
Tests para BenchmarkPlotter y PlotStyle.
Usando el patrón existente del proyecto.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Use non-interactive backend for matplotlib
import matplotlib
matplotlib.use('Agg')

from pathlib import Path
import tempfile


class TestPlotStyle:
    """Tests para PlotStyle."""

    def test_default_values(self):
        from src.visualization.benchmark_plots import PlotStyle

        style = PlotStyle()
        assert style.primary_color == "#003366"
        assert style.secondary_color == "#0066CC"
        assert style.success_color == "#228B22"
        assert style.error_color == "#DC143C"
        assert style.warning_color == "#FF8C00"
        assert style.grid_alpha == 0.3
        assert style.figure_size == (10, 6)
        assert style.font_size == 10

    def test_custom_values(self):
        from src.visualization.benchmark_plots import PlotStyle

        style = PlotStyle(
            primary_color="#FF0000",
            figure_size=(12, 8),
            font_size=12,
        )
        assert style.primary_color == "#FF0000"
        assert style.figure_size == (12, 8)
        assert style.font_size == 12


class TestBenchmarkPlotter:
    """Tests para BenchmarkPlotter."""

    def _create_mock_result(self, solver, problem, status, obj, time_ms):
        from src.core import Solution

        class MockStats:
            solve_time = 0.1
            build_time = 0.01
            iterations = 10
            nodes = 0
            simplex_iterations = 0
            barrier_iterations = 0
            crossover_iterations = 0
            memory_used_mb = 1.0

        class MockResult:
            def __init__(self, solver, problem, status, obj, time_ms):
                self.solver_name = solver
                self.problem_name = problem
                self.problem_text = "test"
                self.solution = Solution(status=status, objective_value=obj, variables={})
                self.stats = MockStats()
                self.total_time = time_ms / 1000
                self.error = None
                self.memory_used_mb = 1.0
                self.peak_memory_mb = 2.0

        return MockResult(solver, problem, status, obj, time_ms)

    def _create_mock_runner(self):
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        runner.results = [
            self._create_mock_result("gurobi", "prob1", "OPTIMAL", 42.0, 100.0),
            self._create_mock_result("highs", "prob1", "OPTIMAL", 42.0, 150.0),
        ]
        return runner

    def test_init_with_runner(self):
        from src.visualization.benchmark_plots import BenchmarkPlotter

        runner = self._create_mock_runner()
        plotter = BenchmarkPlotter(runner)
        assert plotter.runner is runner

    def test_init_with_custom_style(self):
        from src.visualization.benchmark_plots import BenchmarkPlotter, PlotStyle

        runner = self._create_mock_runner()
        style = PlotStyle(font_size=14)
        plotter = BenchmarkPlotter(runner, style=style)
        assert plotter.style.font_size == 14

    def test_plot_times_comparison_empty(self):
        from src.visualization.benchmark_plots import BenchmarkPlotter
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        runner.results = []
        plotter = BenchmarkPlotter(runner)
        plotter.plot_times_comparison()

    def test_plot_success_rate_empty(self):
        from src.visualization.benchmark_plots import BenchmarkPlotter
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        runner.results = []
        plotter = BenchmarkPlotter(runner)
        plotter.plot_success_rate()

    def test_plot_performance_profile_empty(self):
        from src.visualization.benchmark_plots import BenchmarkPlotter
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        runner.results = []
        plotter = BenchmarkPlotter(runner)
        plotter.plot_performance_profile()

    def test_plot_summary_dashboard_empty(self):
        from src.visualization.benchmark_plots import BenchmarkPlotter
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        runner.results = []
        plotter = BenchmarkPlotter(runner)
        plotter.plot_summary_dashboard()

    def test_generate_all_plots_with_results(self):
        from src.visualization.benchmark_plots import BenchmarkPlotter

        runner = self._create_mock_runner()
        plotter = BenchmarkPlotter(runner)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            plotter.generate_all_plots(output_dir)
            assert (output_dir / "benchmark_times.png").exists()
            assert (output_dir / "benchmark_success.png").exists()
            assert (output_dir / "benchmark_profile.png").exists()
            assert (output_dir / "benchmark_dashboard.png").exists()