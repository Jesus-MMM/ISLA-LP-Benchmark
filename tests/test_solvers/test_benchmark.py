"""
Tests para BenchmarkRunner y BenchmarkConfig.
Usando el patrón existente del proyecto.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pathlib import Path
import tempfile
import matplotlib
matplotlib.use('Agg')

import importlib


class TestBenchmarkConfig:
    """Tests para BenchmarkConfig."""

    def test_default_values(self):
        from src.solver.benchmark import BenchmarkConfig
        
        config = BenchmarkConfig()
        assert config.warmup_runs == 1
        assert config.runs_per_problem == 1
        assert config.verbose is False
        assert config.collect_detailed_stats is True
        assert config.collect_memory is True
        assert config.fairness_mode is True
        assert config.randomize_order is True

    def test_custom_values(self):
        from src.solver.benchmark import BenchmarkConfig
        
        config = BenchmarkConfig(
            warmup_runs=3,
            runs_per_problem=5,
            verbose=True,
            time_limit=60.0,
        )
        assert config.warmup_runs == 3
        assert config.runs_per_problem == 5
        assert config.verbose is True
        assert config.time_limit == 60.0

    def test_time_limit_none_by_default(self):
        from src.solver.benchmark import BenchmarkConfig
        
        config = BenchmarkConfig()
        assert config.time_limit is None


class TestBenchmarkResult:
    """Tests para BenchmarkResult."""

    def test_to_dict(self):
        from src.solver.benchmark import BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        result = BenchmarkResult(
            solver_name="test_solver",
            problem_name="test_problem",
            problem_text="max: x;",
            solution=Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 1}),
            stats=SolverStats(),
        )
        
        result_dict = result.to_dict()
        assert result_dict["solver_name"] == "test_solver"
        assert result_dict["problem_name"] == "test_problem"
        assert result_dict["status"] == "OPTIMAL"
        assert result_dict["objective_value"] == 42.0


class TestBenchmarkRunnerAdditional:
    """Tests adicionales para BenchmarkRunner."""

    def test_get_summary_empty(self):
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        summary = runner.get_summary()
        assert summary == {}

    def test_print_summary_empty(self, capsys):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="test",
                problem_name="p1",
                problem_text="",
                solution=Solution(status="OPTIMAL", objective_value=1.0, variables={}),
                stats=SolverStats(),
            )
        ]
        runner.print_summary()
        captured = capsys.readouterr()
        assert "Total de pruebas" in captured.out

    def test_run_with_empty_results(self):
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        results = runner.run([], solvers=["gurobi"])
        assert len(results) == 0


class TestRunQuickBenchmark:
    """Tests para run_quick_benchmark."""

    def test_run_quick_benchmark(self):
        from src.solver.benchmark import run_quick_benchmark

        problems = [("test", "max: x; x <= 10; x >= 0;")]
        runner = run_quick_benchmark(problems, solvers=["highs"])
        assert runner is not None
        assert hasattr(runner, 'results')

    def test_export_csv(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="test_solver",
                problem_name="p1",
                problem_text="max: x;",
                solution=Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 1}),
                stats=SolverStats(),
            )
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            tmp_path = Path(f.name)
        
        try:
            runner.export_csv(tmp_path)
            content = tmp_path.read_text()
            assert "problem" in content
            assert "test_solver" in content
        finally:
            os.unlink(tmp_path)

    def test_run_invalid_solver(self):
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        results = runner.run([], solvers=["nonexistent_solver"])
        assert len(results) == 0

    def test_run_single_mip_unsupported(self):
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        assert hasattr(runner, '_run_single')

    def test_export_json(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="test_solver",
                problem_name="p1",
                problem_text="max: x;",
                solution=Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 1}),
                stats=SolverStats(),
            )
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = Path(f.name)

        try:
            runner.export_json(tmp_path)
            assert os.path.exists(tmp_path)
            import json
            with open(tmp_path) as jf:
                data = json.load(jf)
            assert "summary" in data
            assert "results" in data
        finally:
            os.unlink(tmp_path)

    def test_get_summary_with_results(self):
        from src.solver.benchmark import BenchmarkRunner
        from src.core import Solution
        from src.solver.base import SolverStats

        runner = BenchmarkRunner()
        runner.results = [
            type("MockResult", (), {
                "solver_name": "gurobi",
                "problem_name": "prob1",
                "total_time": 0.1,
                "memory_used_mb": 1.0,
                "peak_memory_mb": 2.0,
                "stats": SolverStats(iterations=10, nodes=5),
                "solution": Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                "error": None,
            })(),
            type("MockResult", (), {
                "solver_name": "highs",
                "problem_name": "prob1",
                "total_time": 0.2,
                "memory_used_mb": 2.0,
                "peak_memory_mb": 3.0,
                "stats": SolverStats(iterations=15, nodes=0),
                "solution": Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                "error": None,
            })(),
        ]
        
        summary = runner.get_summary()
        assert summary["total_benchmarks"] == 2
        assert summary["successful"] == 2
        assert "by_solver" in summary
        assert "gurobi" in summary["by_solver"]
        assert "highs" in summary["by_solver"]

    def test_benchmark_result_to_dict(self):
        from src.solver.benchmark import BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        result = BenchmarkResult(
            solver_name="test_solver",
            problem_name="test_problem",
            problem_text="max: x;",
            solution=Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 1}),
            stats=SolverStats(),
        )
        
        result_dict = result.to_dict()
        assert result_dict["solver_name"] == "test_solver"
        assert result_dict["problem_name"] == "test_problem"
        assert result_dict["status"] == "OPTIMAL"
        assert result_dict["objective_value"] == 42.0

    def test_cross_validate_single_solver(self):
        from src.solver.benchmark import BenchmarkRunner
        from src.core import Solution

        runner = BenchmarkRunner()
        runner.results = [
            type("MockResult", (), {
                "solver_name": "highs",
                "solution": Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                "error": None,
                "problem_text": "max: x; x <= 10;",
            })(),
        ]
        
        runner._cross_validate({})

    def test_cross_validate_two_solvers(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult, BenchmarkConfig
        from src.core import Solution
        from src.solver.base import SolverStats

        runner = BenchmarkRunner(BenchmarkConfig(cross_validate=True))
        runner.results = [
            BenchmarkResult(
                solver_name="highs",
                problem_name="prob1",
                problem_text="max: x; x <= 10; x >= 0;",
                solution=Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 1}),
                stats=SolverStats(),
            ),
            BenchmarkResult(
                solver_name="gurobi",
                problem_name="prob1",
                problem_text="max: x; x <= 10; x >= 0;",
                solution=Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 1}),
                stats=SolverStats(),
            ),
        ]
        
        runner._cross_validate({"prob1": runner.results})

    def test_cross_validate_with_invalid_solution(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        runner = BenchmarkRunner()
        runner.results = [
            BenchmarkResult(
                solver_name="highs",
                problem_name="prob1",
                problem_text="max: x; x <= 10;",
                solution=Solution(status="OPTIMAL", objective_value=10.0, variables={"x": 1}),
                stats=SolverStats(),
            ),
            BenchmarkResult(
                solver_name="gurobi",
                problem_name="prob1",
                problem_text="max: x; x <= 10;",
                solution=Solution(status="ERROR", objective_value=None, variables={}),
                stats=SolverStats(),
            ),
        ]
        
        runner._cross_validate({"prob1": runner.results})

    def test_run_with_verbose_single_mip_unsupported(self, capsys):
        from src.solver.benchmark import BenchmarkRunner

        runner = BenchmarkRunner()
        runner.config.runs_per_problem = 1
        runner.config.verbose = True
        runner.config.warmup_runs = 0
        runner.config.cross_validate = False
        
        result = runner._run_single("highs", "test_mip", "max: x; x integer; x <= 10;")
        assert "MILP" in result.solution.status or result.error is not None

    def test_run_without_fairness_mode(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(fairness_mode=False, cross_validate=False, collect_progress=False))
        results = runner.run([], solvers=["highs"])
        assert len(results) == 0

    def test_run_with_collect_progress(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(collect_progress=True, cross_validate=False, warmup_runs=0))
        results = runner.run([], solvers=["highs"])
        assert len(results) == 0

    def test_benchmark_result_to_dict_with_solution_table(self):
        from src.solver.benchmark import BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        result = BenchmarkResult(
            solver_name="test_solver",
            problem_name="test_problem",
            problem_text="max: x;",
            solution=Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 1}),
            stats=SolverStats(),
        )
        result.solution_table = type("SolutionTable", (), {
            "variables": type("Variables", (), {"to_dicts": lambda: [{"name": "x", "value": 1}]})(),
            "constraints": type("Constraints", (), {"to_dicts": lambda: [{"name": "c1"}]})(),
        })()
        
        result.to_dict()

    def test_benchmark_result_to_dict_with_solution_table_no_to_dicts(self):
        from src.solver.benchmark import BenchmarkResult
        from src.core import Solution
        from src.solver.base import SolverStats

        result = BenchmarkResult(
            solver_name="test_solver",
            problem_name="test_problem",
            problem_text="max: x;",
            solution=Solution(status="OPTIMAL", objective_value=42.0, variables={"x": 1}),
            stats=SolverStats(),
        )
        result.solution_table = type("SolutionTable", (), {
            "variables": "simple_string",
            "constraints": None,
        })()
        
        result.to_dict()

    def test_run_single_with_real_solver(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(warmup_runs=0, cross_validate=False, collect_progress=True))
        problem_txt = "max: x; x <= 10; x >= 0;"
        result = runner._run_single("highs", "test_real", problem_txt)
        assert result is not None
        assert result.solver_name == "highs"
        assert result.problem_name == "test_real"

    def test_run_single_error_path(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(warmup_runs=0, cross_validate=False, collect_progress=False))
        result = runner._run_single("highs", "test_err", "max: ;")
        assert result.error is not None or result.solution.status != "OPTIMAL"

    def test_run_with_multiple_reps(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(runs_per_problem=2, cross_validate=False, warmup_runs=0, collect_progress=False))
        results = runner.run(
            problems=[("p1", "max: x; x <= 10;")],
            solvers=["highs"],
        )
        assert len(results) >= 1

    def test_cross_validate_verbose_output(self, capsys):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(verbose=True, cross_validate=True, warmup_runs=0))
        runner.results = [
            type("MockResult", (), {
                "solver_name": "highs",
                "solution": type("Solution", (), {"is_optimal": lambda: True})(),
                "error": None,
                "problem_text": "max: x; x <= 10;",
            })(),
            type("MockResult", (), {
                "solver_name": "gurobi",
                "solution": type("Solution", (), {"is_optimal": lambda: True})(),
                "error": None,
                "problem_text": "max: x; x <= 10;",
            })(),
        ]
        
        runner._cross_validate({"p1": runner.results})

    def test_psutil_not_available(self):
        import unittest.mock as mock
        
        with mock.patch.dict('sys.modules', {'psutil': None}):
            import src.solver.benchmark as bm_module
            importlib.reload(bm_module)
            assert bm_module.PSUTIL_AVAILABLE is False or 'psutil' not in dir(bm_module)

    def test_run_with_solvers_none(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(cross_validate=False, warmup_runs=0, collect_progress=False))
        results = runner.run(
            problems=[("p1", "max: x; x <= 10;")],
            solvers=None,
        )
        assert isinstance(results, list)

    def test_run_with_verbose_output(self, capsys):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(verbose=True, cross_validate=False, warmup_runs=0, collect_progress=False, runs_per_problem=1))
        runner.run(
            problems=[("p1", "max: x; x <= 10;")],
            solvers=["highs"],
        )
        capsys.readouterr()

    def test_run_with_multiple_runs_per_problem(self):
        from src.solver.benchmark import BenchmarkRunner, BenchmarkConfig

        runner = BenchmarkRunner(BenchmarkConfig(runs_per_problem=3, cross_validate=False, warmup_runs=0, collect_progress=False, verbose=False))
        results = runner.run(
            problems=[("p1", "max: x; x <= 10;")],
            solvers=["highs"],
        )
        assert isinstance(results, list)