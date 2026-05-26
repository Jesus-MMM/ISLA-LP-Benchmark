"""
Orquestador de benchmarking para comparar solvers de programacion lineal.
Permite ejecutar multiples solvers contra multiples problemas y recopilar metricas.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time
import json
import os
import gc
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from ..parser import LPParser
from ..matrix import LPBuilder
from ..core import LinearProblem, Solution
from ..core.solution import ProgressPoint, SolutionTable, to_solution_table
from ..core.verification import verify_solution, compare_solutions
from .base import BaseSolver, SolverStats, SolverRegistry


@dataclass
class BenchmarkResult:
    """Resultado de un benchmark individual."""
    solver_name: str
    problem_name: str
    problem_text: str
    solution: Solution
    stats: SolverStats
    parse_time: float = 0.0
    build_time: float = 0.0
    solve_time: float = 0.0
    total_time: float = 0.0
    memory_used_mb: float = 0.0
    peak_memory_mb: float = 0.0
    error: Optional[str] = None
    # F6-1: Progress log
    progress_log: Optional[list[ProgressPoint]] = None
    # F6-2: Cross-validation result
    cross_validation: Optional[dict] = None  # {solver: {status_match, obj_diff, ...}
    # F6-3: Solution table
    solution_table: Optional[Any] = None  # SolutionTable instance
    
    def to_dict(self) -> dict:
        """Convierte el resultado a diccionario."""
        result = {
            "solver_name": self.solver_name,
            "problem_name": self.problem_name,
            "status": self.solution.status,
            "objective_value": self.solution.objective_value,
            "variables": self.solution.variables,
            "parse_time": self.parse_time,
            "build_time": self.build_time,
            "solve_time": self.solve_time,
            "total_time": self.total_time,
            "memory_used_mb": self.memory_used_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "iterations": self.stats.iterations,
            "nodes": self.stats.nodes,
            "error": self.error,
        }
        # F6-3: Include solution table if available
        if self.solution_table:
            try:
                if hasattr(self.solution_table, 'variables') and self.solution_table.variables is not None:
                    result["solution_table"] = {
                        "variables": self.solution_table.variables.to_dicts() if hasattr(self.solution_table.variables, 'to_dicts') else str(self.solution_table.variables),
                        "constraints": self.solution_table.constraints.to_dicts() if self.solution_table.constraints and hasattr(self.solution_table.constraints, 'to_dicts') else None,
                    }
            except:
                pass
        
        return result


@dataclass
class BenchmarkConfig:
    """Configuración del benchmark."""
    warmup_runs: int = 1
    runs_per_problem: int = 1
    verbose: bool = False
    collect_detailed_stats: bool = True
    collect_memory: bool = True
    output_dir: Optional[Path] = None
    fairness_mode: bool = True
    randomize_order: bool = True
    time_limit: Optional[float] = None
    collect_progress: bool = False
    cross_validate: bool = True


class BenchmarkRunner:
    """
    Orquestador de benchmarking para solvers de PL.
    
    Permite comparar el rendimiento de diferentes solvers
    ejecutandolos contra un conjunto de problemas.
    """
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()
        self.results: List[BenchmarkResult] = []
        self._solver_cache: Dict[str, BaseSolver] = {}
    
    def add_problem(self, problem_text: str, name: Optional[str] = None) -> None:
        """Agrega un problema al benchmark."""
        pass  # Los problemas se pasan en run()
    
    def run(
        self,
        problems: List[tuple[str, str]],
        solvers: Optional[List[str]] = None
    ) -> List[BenchmarkResult]:
        """
        Ejecuta el benchmark.
        
        Args:
            problems: Lista de (nombre, texto_problema)
            solvers: Lista de nombres de solvers. Si es None, usa todos los disponibles.
            
        Returns:
            Lista de resultados del benchmark.
        """
        if solvers is None:
            solvers = SolverRegistry.list_solvers()
        
        self.results = []
        
        # Group results by problem for cross-validation
        problem_results = {}
        
        for problem_name, problem_text in problems:
            if self.config.verbose:
                print(f"\nProblema: {problem_name}")
            
            problem_results[problem_name] = []
            
            for solver_name in solvers:
                if self.config.verbose:
                    print(f"  Solver: {solver_name}")
                
                for rep in range(self.config.runs_per_problem):
                    if self.config.verbose and self.config.runs_per_problem > 1:
                        print(f"    Repeticion: {rep + 1}")
                    
                    result = self._run_single(solver_name, problem_name, problem_text)
                    self.results.append(result)
                    problem_results[problem_name].append(result)
        
        # F6-2: Cross-validation between solvers
        if self.config.cross_validate:
            self._cross_validate(problem_results)
        
        return self.results
    
    def _cross_validate(self, problem_results: dict) -> None:
        """
        Cross-validate solutions between solvers for each problem.
        
        Args:
            problem_results: Dict mapping problem_name to list of BenchmarkResult
        """
        for problem_name, results in problem_results.items():
            if len(results) < 2:
                continue
            
            # Parse problem once for verification
            try:
                problem = LPParser(results[0].problem_text).parse()
            except:
                continue
            
            # Verify each solution
            for result in results:
                if result.error or not result.solution.is_optimal():
                    continue
                
                is_valid, issues = verify_solution(problem, result.solution)
                if not is_valid and self.config.verbose:
                    print(f"  Warning: {result.solver_name} solution invalid for {problem_name}: {issues[:3]}")
            
            # Compare solutions between solvers
            optimal_solutions = [
                (r.solver_name, r.solution) for r in results 
                if r.solution.is_optimal() and not r.error
            ]
            
            if len(optimal_solutions) >= 2:
                solutions = [s for _, s in optimal_solutions]
                warnings = compare_solutions(problem, solutions)
                
                if warnings and self.config.verbose:
                    print(f"  Cross-validation warnings for {problem_name}:")
                    for w in warnings:
                        print(f"    - {w}")
                
                # Store cross-validation results in each BenchmarkResult
                for result in results:
                    if result.solver_name in [s[0] for s in optimal_solutions]:
                        result.cross_validation = {
                            "status": "compared",
                            "warnings": warnings
                        }
    
    def _run_single(
        self, 
        solver_name: str, 
        problem_name: str, 
        problem_text: str
    ) -> BenchmarkResult:
        """Ejecuta un solver contra un problema."""
        total_start = time.perf_counter()
        
        memory_before = 0
        memory_after = 0
        memory_solver_created = 0
        if self.config.collect_memory and PSUTIL_AVAILABLE:
            gc.collect()
            memory_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        
        try:
            parse_start = time.perf_counter()
            problem = LPParser(problem_text).parse()
            parse_time = time.perf_counter() - parse_start
            
            build_start = time.perf_counter()
            lp = LPBuilder(problem).build()
            build_time = time.perf_counter() - build_start
            
            solver_class = SolverRegistry.get(solver_name)
            if solver_class is None:
                raise ValueError(f"Solver '{solver_name}' no encontrado")
            
            # Crear solver con configuracion (verbose + time_limit)
            from src.solver import SolverConfig
            scfg = SolverConfig(
                verbose=self.config.verbose,
                time_limit=self.config.time_limit,
            )
            try:
                solver = solver_class(problem, scfg)
            except TypeError:
                solver = solver_class(problem)
                solver.config = scfg
            
            # Verificar si el solver soporta MILP si el problema es MIP
            if problem.is_mip and not solver.capabilities.milp:
                return BenchmarkResult(
                    solver_name=solver_name,
                    problem_name=problem_name,
                    problem_text=problem_text,
                    solution=Solution(status="ERROR: Solver does not support MILP", objective_value=None, variables={}),
                    stats=SolverStats(),
                    total_time=time.perf_counter() - total_start,
                    error=" la capacidad de MILP no es soportada por este solver"
                )
            
            # F6-5: Measure memory after solver creation (more accurate per-solver)
            if self.config.collect_memory and PSUTIL_AVAILABLE:
                gc.collect()
                memory_solver_created = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            
            # Warmup en la MISMA instancia
            if self.config.warmup_runs > 0:
                for _ in range(self.config.warmup_runs):
                    try:
                        solver.solve()
                    except:
                        pass
                # Reiniciar stats pero mantener estado interno
                solver.reset()
            
            solve_start = time.perf_counter()
            solution = solver.solve()
            solve_time = time.perf_counter() - solve_start
            
            stats = solver.get_stats()
            
            total_time = time.perf_counter() - total_start
            
            if self.config.collect_memory and PSUTIL_AVAILABLE:
                gc.collect()
                memory_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                # F6-5: Use per-solver memory (after solver creation) for more accuracy
                if memory_solver_created > 0:
                    memory_used = max(0, memory_after - memory_solver_created)
                else:
                    memory_used = max(0, memory_after - memory_before)
                peak_memory = memory_after
            else:
                memory_used = 0
                peak_memory = 0
            
            # F6-1: Collect progress log if enabled
            progress_log = None
            if self.config.collect_progress and stats.progress_log:
                progress_log = stats.progress_log
            
            # F6-2: Cross-validation will be done after all solvers run
            
            # F6-3: Generate solution table
            solution_table = None
            try:
                if solution.is_optimal():
                    solution_table = to_solution_table(solution, problem)
            except:
                pass
            
            result = BenchmarkResult(
                solver_name=solver_name,
                problem_name=problem_name,
                problem_text=problem_text,
                solution=solution,
                stats=stats,
                parse_time=parse_time,
                build_time=build_time,
                solve_time=solve_time,
                total_time=total_time,
                memory_used_mb=memory_used,
                peak_memory_mb=peak_memory,
                progress_log=progress_log
            )
            
            # Store solution table for export (F6-3)
            if solution_table:
                result.solution_table = solution_table
            
            return result
            
        except Exception as e:
            total_time = time.perf_counter() - total_start
            return BenchmarkResult(
                solver_name=solver_name,
                problem_name=problem_name,
                problem_text=problem_text,
                solution=Solution(status="ERROR", objective_value=None, variables={}),
                stats=SolverStats(),
                total_time=total_time,
                error=str(e)
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de los resultados."""
        if not self.results:
            return {}
        
        summary = {
            "total_benchmarks": len(self.results),
            "successful": sum(1 for r in self.results if r.solution.is_optimal()),
            "failed": sum(1 for r in self.results if r.error is not None),
            "by_solver": {},
            "by_problem": {}
        }
        
        for result in self.results:
            solver = result.solver_name
            problem = result.problem_name
            
            if solver not in summary["by_solver"]:
                summary["by_solver"][solver] = {
                    "runs": 0,
                    "avg_time": 0,
                    "min_time": float('inf'),
                    "max_time": 0,
                    "times": [],
                    "total_time": 0,
                    "successful": 0,
                    "avg_memory": 0,
                    "peak_memory": 0,
                    "total_iterations": 0,
                    "total_nodes": 0
                }
            
            summary["by_solver"][solver]["runs"] += 1
            summary["by_solver"][solver]["total_time"] += result.total_time
            summary["by_solver"][solver]["times"].append(result.total_time)
            summary["by_solver"][solver]["min_time"] = min(summary["by_solver"][solver]["min_time"], result.total_time)
            summary["by_solver"][solver]["max_time"] = max(summary["by_solver"][solver]["max_time"], result.total_time)
            summary["by_solver"][solver]["total_iterations"] += result.stats.iterations
            summary["by_solver"][solver]["total_nodes"] += result.stats.nodes
            if result.memory_used_mb > 0:
                summary["by_solver"][solver]["avg_memory"] += result.memory_used_mb
            if result.peak_memory_mb > 0:
                summary["by_solver"][solver]["peak_memory"] = max(
                    summary["by_solver"][solver]["peak_memory"],
                    result.peak_memory_mb
                )
            
            if result.solution.is_optimal():
                summary["by_solver"][solver]["successful"] += 1
            
            if problem not in summary["by_problem"]:
                summary["by_problem"][problem] = {
                    "runs": 0,
                    "solved_by": []
                }
            
            summary["by_problem"][problem]["runs"] += 1
            if result.solution.is_optimal():
                summary["by_problem"][problem]["solved_by"].append(solver)
        
        for solver in summary["by_solver"]:
            if summary["by_solver"][solver]["runs"] > 0:
                data = summary["by_solver"][solver]
                data["avg_time"] = data["total_time"] / data["runs"]
                if data["min_time"] == float('inf'):
                    data["min_time"] = 0
                if len(data["times"]) > 1:
                    import numpy as np
                    data["std_time"] = np.std(data["times"])
                else:
                    data["std_time"] = 0
                del data["times"]
                if data["avg_memory"] > 0:
                    data["avg_memory"] = data["avg_memory"] / data["runs"]
        
        return summary
    
    def export_json(self, path: Path) -> None:
        """Exporta los resultados a JSON."""
        data = {
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results]
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_csv(self, path: Path) -> None:
        """Exporta los resultados a CSV."""
        import csv
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "solver", "problem", "status", "objective_value",
                "parse_time", "build_time", "solve_time", "total_time",
                "iterations", "nodes", "error"
            ])
            
            for r in self.results:
                writer.writerow([
                    r.solver_name,
                    r.problem_name,
                    r.solution.status,
                    r.solution.objective_value,
                    f"{r.parse_time:.6f}",
                    f"{r.build_time:.6f}",
                    f"{r.solve_time:.6f}",
                    f"{r.total_time:.6f}",
                    r.stats.iterations,
                    r.stats.nodes,
                    r.error or ""
                ])
    
    def print_summary(self) -> None:
        """Imprime un resumen en consola."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        print(f"Total de pruebas: {summary['total_benchmarks']}")
        print(f"Exitosas: {summary['successful']}")
        print(f"Fallidas: {summary['failed']}")
        
        print("\nPor Solver:")
        print("-"*60)
        print(f"{'Solver':<15} {'Runs':<8} {'Exitosos':<10} {'Tiempo Promedio':<15}")
        print("-"*60)
        
        for solver, data in summary["by_solver"].items():
            print(f"{solver:<15} {data['runs']:<8} {data['successful']:<10} {data['avg_time']*1000:.6f}ms")
        
        print("\n" + "="*60)


def run_quick_benchmark(
    problems: List[tuple[str, str]],
    solvers: Optional[List[str]] = None
) -> BenchmarkRunner:
    """
    Ejecuta un benchmark rapido.
    
    Args:
        problems: Lista de (nombre, texto_problema)
        solvers: Lista de nombres de solvers.
        
    Returns:
        BenchmarkRunner con los resultados.
    """
    config = BenchmarkConfig(verbose=False, runs_per_problem=1)
    runner = BenchmarkRunner(config)
    runner.run(problems, solvers)
    return runner
