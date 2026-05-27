"""
Tests para el modulo benchmark (CLI).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pathlib import Path
from unittest.mock import patch, MagicMock


class TestRunBenchmark:
    """Tests para run_benchmark."""

    def test_benchmark_with_input_file(self):
        # Mock the visualization module before importing benchmark
        import types
        mock_viz_module = types.ModuleType('src.visualization.benchmark_plots')
        mock_viz_module.BenchmarkPlotter = type('_MockBenchmarkPlotter', (), {'__init__': lambda self, *a, **kw: None, 'generate_all_plots': lambda self, *a, **kw: None})
        mock_viz_module.PlotStyle = type('_MockPlotStyle', (), {})
        sys.modules['src.visualization.benchmark_plots'] = mock_viz_module
        
        from src.cli.benchmark import run_benchmark
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with patch("src.cli.benchmark._console"):
                with patch("src.cli.benchmark.BenchmarkRunner") as mock_runner:
                    instance = MagicMock()
                    instance.run.return_value = []
                    instance.print_summary.return_value = ""
                    instance.export_csv.return_value = None
                    mock_runner.return_value = instance
                    with patch("src.cli.benchmark.get_system_info"):
                        rc = run_benchmark(
                            input_path=Path(tmp),
                            solvers=["gurobi"],
                        )
                        assert rc == 0
        finally:
            os.unlink(tmp)
            del sys.modules['src.visualization.benchmark_plots']

    def test_benchmark_without_input(self):
        import types
        mock_viz_module = types.ModuleType('src.visualization.benchmark_plots')
        mock_viz_module.BenchmarkPlotter = type('_MockBenchmarkPlotter', (), {'__init__': lambda self, *a, **kw: None, 'generate_all_plots': lambda self, *a, **kw: None})
        mock_viz_module.PlotStyle = type('_MockPlotStyle', (), {})
        sys.modules['src.visualization.benchmark_plots'] = mock_viz_module
        
        from src.cli.benchmark import run_benchmark
        
        with patch("src.cli.benchmark._console"):
            with patch("src.cli.benchmark.BenchmarkRunner") as mock_runner:
                instance = MagicMock()
                instance.run.return_value = []
                instance.print_summary.return_value = ""
                instance.export_csv.return_value = None
                mock_runner.return_value = instance
                with patch("src.cli.benchmark.get_system_info"):
                    rc = run_benchmark(solvers=["gurobi"])
                    assert rc == 0
        del sys.modules['src.visualization.benchmark_plots']

    def test_benchmark_with_multi_problems(self):
        import types
        mock_viz_module = types.ModuleType('src.visualization.benchmark_plots')
        mock_viz_module.BenchmarkPlotter = type('_MockBenchmarkPlotter', (), {'__init__': lambda self, *a, **kw: None, 'generate_all_plots': lambda self, *a, **kw: None})
        mock_viz_module.PlotStyle = type('_MockPlotStyle', (), {})
        sys.modules['src.visualization.benchmark_plots'] = mock_viz_module
        
        from src.cli.benchmark import run_benchmark
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;\n---\nmin: x + y;\n x + y <= 5;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with patch("src.cli.benchmark._console"):
                with patch("src.cli.benchmark.BenchmarkRunner") as mock_runner:
                    instance = MagicMock()
                    instance.run.return_value = []
                    instance.print_summary.return_value = ""
                    instance.export_csv.return_value = None
                    mock_runner.return_value = instance
                    with patch("src.cli.benchmark.get_system_info"):
                        rc = run_benchmark(
                            input_path=Path(tmp),
                            solvers=["gurobi"],
                        )
                        assert rc == 0
        finally:
            os.unlink(tmp)
            del sys.modules['src.visualization.benchmark_plots']

    def test_benchmark_with_csv_export(self):
        import types
        mock_viz_module = types.ModuleType('src.visualization.benchmark_plots')
        mock_viz_module.BenchmarkPlotter = type('_MockBenchmarkPlotter', (), {'__init__': lambda self, *a, **kw: None, 'generate_all_plots': lambda self, *a, **kw: None})
        mock_viz_module.PlotStyle = type('_MockPlotStyle', (), {})
        sys.modules['src.visualization.benchmark_plots'] = mock_viz_module
        
        from src.cli.benchmark import run_benchmark
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with patch("src.cli.benchmark._console"):
                with patch("src.cli.benchmark.BenchmarkRunner") as mock_runner:
                    instance = MagicMock()
                    instance.run.return_value = []
                    instance.print_summary.return_value = ""
                    instance.export_csv.return_value = None
                    mock_runner.return_value = instance
                    with patch("src.cli.benchmark.get_system_info"):
                        with patch("src.cli.benchmark.export_benchmark_results"):
                            rc = run_benchmark(
                                input_path=Path(tmp),
                                solvers=["gurobi"],
                                output_csv="test.csv",
                            )
                            assert rc == 0
        finally:
            os.unlink(tmp)
            del sys.modules['src.visualization.benchmark_plots']