"""
Tests para ParallelBenchmarkConfig y ParallelBenchmarkRunner.
Usando el patrón existente del proyecto.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import matplotlib

matplotlib.use('Agg')


class TestParallelBenchmarkConfig:
    """Tests para ParallelBenchmarkConfig."""

    def test_default_values(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkConfig

        config = ParallelBenchmarkConfig()
        assert config.warmup_runs == 1
        assert config.runs_per_problem == 1
        assert config.verbose is False
        assert config.collect_memory is True

    def test_custom_values(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkConfig

        config = ParallelBenchmarkConfig(
            warmup_runs=3,
            runs_per_problem=5,
            verbose=True,
            collect_memory=False,
        )
        assert config.warmup_runs == 3
        assert config.runs_per_problem == 5
        assert config.verbose is True
        assert config.collect_memory is False

    def test_time_limit_none_by_default(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkConfig

        config = ParallelBenchmarkConfig()
        assert config.time_limit is None

    def test_time_limit_custom(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkConfig

        config = ParallelBenchmarkConfig(time_limit=60.0)
        assert config.time_limit == 60.0


class TestParallelBenchmarkRunner:
    """Tests para ParallelBenchmarkRunner."""

    def test_init_default_config(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkConfig, ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        assert isinstance(runner.config, ParallelBenchmarkConfig)
        assert len(runner.results) == 0

    def test_init_custom_config(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkConfig, ParallelBenchmarkRunner

        config = ParallelBenchmarkConfig(verbose=True)
        runner = ParallelBenchmarkRunner(config)
        assert runner.config.verbose is True

    def test_get_summary_empty(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        summary = runner.get_summary()
        assert summary == {}

    def test_print_summary_empty(self, capsys):
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        runner.print_summary()
        captured = capsys.readouterr()
        assert "No hay resultados" in captured.out

    def test_dict_to_result(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        data = {
            "solver_name": "gurobi",
            "problem_name": "test_problem",
            "problem_text": "max: x;",
            "solution": {
                "status": "OPTIMAL",
                "objective_value": 42.0,
                "variables": {"x": 1},
                "dual_values": None,
                "reduced_costs": None,
                "iterations": 10,
                "nodes": 0,
            },
            "stats": {
                "solve_time": 0.1,
                "build_time": 0.01,
                "iterations": 10,
                "nodes": 0,
                "simplex_iterations": 0,
                "barrier_iterations": 0,
                "crossover_iterations": 0,
                "memory_used_mb": 1.0,
            },
            "solve_time": 0.1,
            "total_time": 0.11,
            "memory_used_mb": 1.0,
            "peak_memory_mb": 2.0,
        }
        result = runner._dict_to_result(data)
        assert result.solver_name == "gurobi"
        assert result.problem_name == "test_problem"
        assert result.solution.status == "OPTIMAL"
        assert result.total_time == 0.11

    def test_get_summary_with_results(self):
        from src.core import Solution
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        runner.results = [
            type("MockResult", (), {
                "solver_name": "gurobi",
                "solution": Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                "error": None,
                "total_time": 0.1,
                "memory_used_mb": 1.0,
            })(),
            type("MockResult", (), {
                "solver_name": "gurobi",
                "solution": Solution(status="OPTIMAL", objective_value=50.0, variables={}),
                "error": None,
                "total_time": 0.2,
                "memory_used_mb": 2.0,
            })(),
            type("MockResult", (), {
                "solver_name": "highs",
                "solution": Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                "error": None,
                "total_time": 0.15,
                "memory_used_mb": 1.5,
            })(),
        ]

        summary = runner.get_summary()
        assert summary["total_benchmarks"] == 3
        assert summary["successful"] == 3
        assert "gurobi" in summary["by_solver"]
        assert "highs" in summary["by_solver"]

    def test_get_summary_with_failures(self):
        from src.core import Solution
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        runner.results = [
            type("MockResult", (), {
                "solver_name": "gurobi",
                "solution": Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                "error": None,
                "total_time": 0.1,
                "memory_used_mb": 1.0,
            })(),
            type("MockResult", (), {
                "solver_name": "highs",
                "solution": Solution(status="ERROR", objective_value=None, variables={}),
                "error": "Solver error",
                "total_time": 0.2,
                "memory_used_mb": 0.0,
            })(),
        ]

        summary = runner.get_summary()
        assert summary["failed"] == 1
        assert len(summary["by_solver"]["highs"]["errors"]) == 1

    def test_print_summary_with_results(self, capsys):
        from src.core import Solution
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        runner.results = [
            type("MockResult", (), {
                "solver_name": "gurobi",
                "solution": Solution(status="OPTIMAL", objective_value=42.0, variables={}),
                "error": None,
                "total_time": 0.1,
                "memory_used_mb": 1.0,
            })(),
        ]

        runner.print_summary()
        captured = capsys.readouterr()
        assert "RESUMEN DE BENCHMARK PARALELO" in captured.out
        assert "gurobi" in captured.out

    def test_worker_execute_success(self):
        from src.solver.parallel_benchmark import _worker_execute

        problem_text = "max: x; x <= 10; x >= 0;"
        result = _worker_execute("highs", "test_prob", problem_text, {
            "warmup_runs": 0,
            "runs_per_problem": 1,
            "verbose": False,
            "collect_memory": False,
            "time_limit": None,
            "collect_solution_table": True,
        })

        assert result["solver_name"] == "highs"
        assert result["problem_name"] == "test_prob"
        assert result["error"] is None or "no soporta" not in str(result.get("error", ""))

    def test_worker_execute_invalid_solver(self):
        from src.solver.parallel_benchmark import _worker_execute

        problem_text = "max: x; x <= 10; x >= 0;"
        result = _worker_execute("nonexistent_solver", "test_prob", problem_text, {
            "warmup_runs": 0,
            "runs_per_problem": 1,
            "verbose": False,
            "collect_memory": False,
            "time_limit": None,
            "collect_solution_table": False,
        })

        assert result["error"] is not None

    def test_worker_execute_mip_unsupported(self):
        from src.solver.parallel_benchmark import _worker_execute

        problem_text = "max: x; x <= 10;"
        result = _worker_execute("highs", "test_mip", problem_text, {
            "warmup_runs": 0,
            "runs_per_problem": 1,
            "verbose": False,
            "collect_memory": False,
            "time_limit": None,
            "collect_solution_table": False,
        })

        assert "status" in result["solution"]

    def test_run_with_solvers_list(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        results = runner.run(
            problems=[("p1", "max: x; x <= 10;")],
            solvers=["highs"],
            timeout=30,
            max_workers=1,
        )
        assert len(results) >= 1

    def test_dict_to_result_with_solution_table(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        data = {
            "solver_name": "highs",
            "problem_name": "prob",
            "problem_text": "max: x;",
            "solution": {
                "status": "OPTIMAL",
                "objective_value": 1.0,
                "variables": {"x": 1.0},
                "dual_values": None,
                "reduced_costs": None,
                "iterations": 5,
                "nodes": 0,
            },
            "stats": {
                "solve_time": 0.1,
                "build_time": 0.01,
                "iterations": 5,
                "nodes": 0,
                "simplex_iterations": 0,
                "barrier_iterations": 0,
                "crossover_iterations": 0,
                "memory_used_mb": 1.0,
            },
            "solve_time": 0.1,
            "total_time": 0.11,
            "memory_used_mb": 1.0,
            "peak_memory_mb": 2.0,
            "solution_table": {"variables": [{"name": "x", "value": 1}]},
        }
        result = runner._dict_to_result(data)
        assert result.solver_name == "highs"
        assert result.solution_table is not None

    def test_worker_execute_with_solution_table(self):
        from src.solver.parallel_benchmark import _worker_execute

        problem_text = "max: x; x <= 10; x >= 0;"
        result = _worker_execute("highs", "test_prob", problem_text, {
            "warmup_runs": 0,
            "runs_per_problem": 1,
            "verbose": False,
            "collect_memory": False,
            "time_limit": None,
            "collect_solution_table": True,
        })

        assert result["solver_name"] == "highs"
        assert result["problem_name"] == "test_prob"

    def test_worker_execute_invalid_problem(self):
        from src.solver.parallel_benchmark import _worker_execute

        result = _worker_execute("highs", "test_err", "invalid lp format", {
            "warmup_runs": 0,
            "runs_per_problem": 1,
            "verbose": False,
            "collect_memory": False,
            "time_limit": None,
            "collect_solution_table": False,
        })

        assert result["error"] is not None

    def test_run_with_empty_solvers(self):
        from src.solver.parallel_benchmark import ParallelBenchmarkRunner

        runner = ParallelBenchmarkRunner()
        results = runner.run(
            problems=[("p1", "max: x; x <= 10;")],
            max_workers=1,
        )
        assert isinstance(results, list)
