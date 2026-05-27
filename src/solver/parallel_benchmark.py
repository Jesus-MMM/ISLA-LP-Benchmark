"""
Ejecucion de benchmarks en procesos paralelos aislados.

Cada instancia (problema, solver) se ejecuta en un proceso independiente
para proteger contra segfaults, fugas de memoria y garantizar aislamiento.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, List
import time
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

from ..parser import LPParser
from ..core import Solution
from ..core.solution import to_solution_table
from .base import SolverRegistry

from .benchmark import BenchmarkResult


@dataclass
class ParallelBenchmarkConfig:
    """Configuracion del benchmark paralelo."""
    warmup_runs: int = 1
    runs_per_problem: int = 1
    verbose: bool = False
    collect_memory: bool = True
    output_dir: Optional[Path] = None
    time_limit: Optional[float] = None
    collect_solution_table: bool = True


def _worker_execute(
    solver_name: str,
    problem_name: str,
    problem_text: str,
    config_dict: dict,
) -> dict:
    """Ejecuta un solver contra un problema en un proceso aislado.

    Args:
        solver_name: Nombre del solver a utilizar.
        problem_name: Nombre del problema.
        problem_text: Texto del problema en formato LP.
        config_dict: Diccionario con la configuracion del benchmark.

    Returns:
        Diccionario con los resultados serializables.
    """
    cfg = ParallelBenchmarkConfig(**config_dict)
    total_start = time.perf_counter()
    mem_before = 0.0

    try:
        import psutil as _psutil
        mem_before = _psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        pass

    result_dict = {
        "solver_name": solver_name,
        "problem_name": problem_name,
        "problem_text": problem_text,
        "error": None,
        "parse_time": 0.0,
        "build_time": 0.0,
        "solve_time": 0.0,
        "total_time": 0.0,
        "memory_used_mb": 0.0,
        "peak_memory_mb": 0.0,
    }

    try:
        parse_start = time.perf_counter()
        problem = LPParser(problem_text).parse()
        result_dict["parse_time"] = time.perf_counter() - parse_start

        solver_class = SolverRegistry.get(solver_name)
        if solver_class is None:
            raise ValueError(f"Solver '{solver_name}' no encontrado")

        from ..solver import SolverConfig
        scfg = SolverConfig(
            verbose=cfg.verbose,
            time_limit=cfg.time_limit or 0,
        )
        try:
            solver = solver_class(problem, scfg)
        except TypeError:
            solver = solver_class(problem)
            solver.config = scfg

        if problem.is_mip and not solver.capabilities.milp:
            return {
                **result_dict,
                "solution": {
                    "status": "ERROR: Solver does not support MILP",
                    "objective_value": None,
                    "variables": {},
                },
                "stats": {"solve_time": 0.0},
                "error": "MILP no soportado por este solver",
            }

        for _ in range(cfg.warmup_runs):
            try:
                solver.solve()
            except Exception:
                pass
        solver.reset()

        mem_peak = 0.0
        try:
            import psutil as _psutil
            proc = _psutil.Process(os.getpid())
        except Exception:
            proc = None

        solve_start = time.perf_counter()
        solution = solver.solve()
        solve_time = time.perf_counter() - solve_start

        try:
            if proc:
                mem_after = proc.memory_info().rss / (1024 * 1024)
                mem_peak = proc.memory_info().rss / (1024 * 1024)
                result_dict["memory_used_mb"] = mem_after - mem_before
                result_dict["peak_memory_mb"] = mem_peak - mem_before
        except Exception:
            pass

        stats = solver.get_stats()

        solution_table = None
        if cfg.collect_solution_table and solution.is_optimal():
            try:
                solution_table = to_solution_table(solution, problem)
            except Exception:
                pass

        result_dict.update({
            "solution": {
                "status": solution.status,
                "objective_value": solution.objective_value,
                "variables": solution.variables,
                "dual_values": solution.dual_values,
                "reduced_costs": solution.reduced_costs,
                "iterations": solution.iterations,
                "nodes": solution.nodes,
            },
            "stats": {
                "solve_time": stats.solve_time,
                "build_time": stats.build_time,
                "iterations": stats.iterations,
                "nodes": stats.nodes,
                "simplex_iterations": stats.simplex_iterations,
                "barrier_iterations": stats.barrier_iterations,
                "crossover_iterations": stats.crossover_iterations,
                "memory_used_mb": stats.memory_used_mb,
            },
            "solve_time": solve_time,
            "total_time": time.perf_counter() - total_start,
        })

        if solution_table is not None:
            result_dict["solution_table"] = solution_table

    except Exception as e:
        result_dict.update({
            "error": str(e),
            "solution": {
                "status": "ERROR",
                "objective_value": None,
                "variables": {},
            },
            "stats": {"solve_time": 0.0},
            "total_time": time.perf_counter() - total_start,
        })

    return result_dict


class ParallelBenchmarkRunner:
    """Ejecuta benchmarks en procesos paralelos aislados.

    Cada combinacion (problema, solver, repeticion) se ejecuta en un
    proceso independiente, protegiendo contra segfaults y garantizando
    que no haya interferencia entre ejecuciones.

    Ejemplo:
        runner = ParallelBenchmarkRunner()
        results = runner.run(
            problems=[("prob1", problem_text)],
            solvers=["highs", "glpk"],
            timeout=120,
            max_workers=2,
        )
    """

    def __init__(self, config: Optional[ParallelBenchmarkConfig] = None):
        """Inicializa el runner con configuracion opcional."""
        self.config = config or ParallelBenchmarkConfig()
        self.results: List[BenchmarkResult] = []

    def run(
        self,
        problems: List[tuple[str, str]],
        solvers: Optional[List[str]] = None,
        timeout: int = 300,
        max_workers: Optional[int] = None,
    ) -> List[BenchmarkResult]:
        """Ejecuta el benchmark en paralelo.

        Args:
            problems: Lista de (nombre, texto_del_problema).
            solvers: Lista de nombres de solvers. Si es None, usa todos disponibles.
            timeout: Timeout maximo por instancia en segundos.
            max_workers: Numero maximo de workers. Default: CPU count.

        Returns:
            Lista de resultados del benchmark.
        """
        if solvers is None:
            solvers = SolverRegistry.list_solvers()

        if max_workers is None:
            max_workers = multiprocessing.cpu_count()

        self.results = []
        config_dict = asdict(self.config)
        tasks = []

        for problem_name, problem_text in problems:
            for solver_name in solvers:
                for _ in range(self.config.runs_per_problem):
                    tasks.append((solver_name, problem_name, problem_text, config_dict))

        if not tasks:
            return self.results

        if self.config.verbose:
            print(f"Lanzando {len(tasks)} tareas con {max_workers} workers...")

        futures = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for task in tasks:
                future = executor.submit(_worker_execute, *task)
                futures.append(future)

            for future in as_completed(futures, timeout=timeout * len(tasks)):
                try:
                    result_data = future.result(timeout=timeout)
                    result = self._dict_to_result(result_data)
                    self.results.append(result)
                except TimeoutError:
                    self.results.append(BenchmarkResult(
                        solver_name="unknown",
                        problem_name="unknown",
                        problem_text="",
                        solution=Solution(status="TIMEOUT", objective_value=None, variables={}),
                        stats=type("Stats", (), {"solve_time": 0.0})(),
                        error="Timeout excedido",
                        total_time=timeout,
                    ))
                except Exception as e:
                    self.results.append(BenchmarkResult(
                        solver_name="unknown",
                        problem_name="unknown",
                        problem_text="",
                        solution=Solution(status="ERROR", objective_value=None, variables={}),
                        stats=type("Stats", (), {"solve_time": 0.0})(),
                        error=str(e),
                    ))

        return self.results

    def _dict_to_result(self, data: dict) -> BenchmarkResult:
        """Convierte un diccionario de resultados a BenchmarkResult."""
        sol_data = data.get("solution", {})
        solution = Solution(
            status=sol_data.get("status", "UNKNOWN"),
            objective_value=sol_data.get("objective_value"),
            variables=sol_data.get("variables", {}),
            dual_values=sol_data.get("dual_values"),
            reduced_costs=sol_data.get("reduced_costs"),
            iterations=sol_data.get("iterations", 0),
            nodes=sol_data.get("nodes", 0),
        )

        st_data = data.get("stats", {})
        from .base import SolverStats
        stats = SolverStats(
            solve_time=st_data.get("solve_time", 0.0),
            build_time=st_data.get("build_time", 0.0),
            iterations=st_data.get("iterations", 0),
            nodes=st_data.get("nodes", 0),
            simplex_iterations=st_data.get("simplex_iterations", 0),
            barrier_iterations=st_data.get("barrier_iterations", 0),
            crossover_iterations=st_data.get("crossover_iterations", 0),
            memory_used_mb=st_data.get("memory_used_mb", 0.0),
        )

        return BenchmarkResult(
            solver_name=data.get("solver_name", "unknown"),
            problem_name=data.get("problem_name", "unknown"),
            problem_text=data.get("problem_text", ""),
            solution=solution,
            stats=stats,
            parse_time=data.get("parse_time", 0.0),
            build_time=data.get("build_time", 0.0),
            solve_time=data.get("solve_time", 0.0),
            total_time=data.get("total_time", 0.0),
            memory_used_mb=data.get("memory_used_mb", 0.0),
            peak_memory_mb=data.get("peak_memory_mb", 0.0),
            error=data.get("error"),
            solution_table=data.get("solution_table"),
        )

    def get_summary(self) -> dict:
        """Obtiene un resumen estadistico de los resultados."""
        if not self.results:
            return {}

        by_solver: dict = {}
        for r in self.results:
            if r.solver_name not in by_solver:
                by_solver[r.solver_name] = {
                    "runs": 0,
                    "successful": 0,
                    "failed": 0,
                    "times": [],
                    "errors": [],
                }
            s = by_solver[r.solver_name]
            s["runs"] += 1
            if r.error or not r.solution.is_optimal():
                s["failed"] += 1
                if r.error:
                    s["errors"].append(r.error)
            else:
                s["successful"] += 1
            s["times"].append(r.total_time)

        for solver_name, sdata in by_solver.items():
            times = sdata.pop("times", [])
            sdata["avg_time"] = sum(times) / len(times) if times else 0.0
            sdata["min_time"] = min(times) if times else 0.0
            sdata["max_time"] = max(times) if times else 0.0

            mem_values = [
                r.memory_used_mb for r in self.results
                if r.solver_name == solver_name
            ]
            sdata["avg_memory_mb"] = (
                sum(mem_values) / len(mem_values) if mem_values else 0.0
            )

        return {
            "total_benchmarks": len(self.results),
            "successful": sum(1 for r in self.results if r.solution.is_optimal()),
            "failed": sum(1 for r in self.results if r.error or not r.solution.is_optimal()),
            "by_solver": by_solver,
        }

    def print_summary(self) -> None:
        """Imprime un resumen formateado en consola."""
        summary = self.get_summary()
        if not summary:
            print("No hay resultados para mostrar.")
            return

        print("=" * 60)
        print("RESUMEN DE BENCHMARK PARALELO")
        print("=" * 60)
        print(f"Total de pruebas: {summary['total_benchmarks']}")
        print(f"Exitosas: {summary['successful']}")
        print(f"Fallidas: {summary['failed']}")
        print()
        print(f"{'Solver':<20} {'Runs':<8} {'Exitosos':<10} {'Tiempo Prom.':<12}")
        print("-" * 50)
        for solver_name, sdata in sorted(summary["by_solver"].items()):
            avg_ms = sdata.get("avg_time", 0) * 1000
            print(f"{solver_name:<20} {sdata['runs']:<8} {sdata['successful']:<10} {avg_ms:.2f}ms")
        print("=" * 60)
