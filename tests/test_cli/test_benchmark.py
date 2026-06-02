"""
Tests para el modulo benchmark (CLI).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestRunBenchmark:
    """Tests para run_benchmark."""

    def test_benchmark_with_input_file(self):
        import tempfile

        from src.cli.benchmark import run_benchmark
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
                    with patch("src.cli.get_system_info"):
                        rc = run_benchmark(
                            input_path=Path(tmp),
                            solvers=["gurobi"],
                        )
                        assert rc == 0
        finally:
            os.unlink(tmp)

    def test_benchmark_without_input(self):
        from src.cli.benchmark import run_benchmark

        with patch("src.cli.benchmark._console"):
            with patch("src.cli.benchmark.BenchmarkRunner") as mock_runner:
                instance = MagicMock()
                instance.run.return_value = []
                instance.print_summary.return_value = ""
                instance.export_csv.return_value = None
                mock_runner.return_value = instance
                with patch("src.cli.get_system_info"):
                    rc = run_benchmark(solvers=["gurobi"])
                    assert rc == 0

    def test_benchmark_with_multi_problems(self):
        import tempfile

        from src.cli.benchmark import run_benchmark
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
                    with patch("src.cli.get_system_info"):
                        rc = run_benchmark(
                            input_path=Path(tmp),
                            solvers=["gurobi"],
                        )
                        assert rc == 0
        finally:
            os.unlink(tmp)

    def test_benchmark_with_csv_export(self):
        import tempfile

        from src.cli.benchmark import run_benchmark
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
                    with patch("src.cli.get_system_info"):
                        with patch("src.analysis.export_benchmark_results"):
                            rc = run_benchmark(
                                input_path=Path(tmp),
                                solvers=["gurobi"],
                                output_csv="test.csv",
                            )
                            assert rc == 0
        finally:
            os.unlink(tmp)
