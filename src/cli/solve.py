"""
Handler para resolver problemas individuales de programacion lineal.
"""

import time
from pathlib import Path
from typing import Optional

from src.parser import LPParser
from src.solver import SolverConfig, SolverRegistry
from src.visualization import LinearVisualization


def solve_single(
    input_path: Path,
    solver_name: str = "highs",
    visualize: bool = False,
    pdf: bool = False,
    times: bool = False,
    verbose: bool = False,
    output: Optional[str] = None,
    quiet: bool = False,
    json_output: bool = False,
    time_limit: Optional[float] = None,
) -> int:
    """Resuelve un problema individual."""
    if not input_path.exists():
        print(f"Error: Archivo no encontrado: {input_path}")
        return 1

    start_total = time.perf_counter()

    try:
        solver_class = SolverRegistry.get(solver_name)
        if solver_class is None:
            print(f"Error: Solver '{solver_name}' no encontrado")
            return 1

        with open(input_path, 'r') as f:
            problem_text = f.read()

        start_parse = time.perf_counter()
        problem = LPParser(problem_text).parse()
        parse_time = time.perf_counter() - start_parse

        start_build = time.perf_counter()
        build_time = time.perf_counter() - start_build

        config = SolverConfig(verbose=verbose, time_limit=time_limit)
        start_solve = time.perf_counter()
        try:
            solver = solver_class(problem, config)
        except TypeError:
            solver = solver_class(problem)
            solver.config = config
        solution = solver.solve()
        solve_time = time.perf_counter() - start_solve

        total_time = time.perf_counter() - start_total

        # JSON output
        if json_output:
            import json
            result = {
                "solver": solver_name,
                "status": solution.status,
                "objective_value": solution.objective_value,
                "variables": solution.variables,
                "times": {
                    "parse_ms": round(parse_time * 1000, 4),
                    "build_ms": round(build_time * 1000, 4),
                    "solve_ms": round(solve_time * 1000, 4),
                    "total_ms": round(total_time * 1000, 4),
                },
            }
            output_path = output or None
            if output_path and output_path.endswith(".json"):
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
                if not quiet:
                    print(f"JSON saved to: {output_path}")
            else:
                print(json.dumps(result, indent=2))
            return 0

        # Normal output
        if not quiet:
            if solution.is_optimal():
                print(f"Optimal value: {solution.objective_value:.4f}")
                for var, value in solution.variables.items():
                    print(f"  {var} = {value:.4f}")
            else:
                print(f"Status: {solution.status}")

        if visualize and len(problem.variables) == 2:
            output_path = output or str(input_path.with_suffix('.png'))
            viz = LinearVisualization(problem, solution)
            viz.plot(save_path=str(output_path), show=False)
            if not quiet:
                print(f"Graph saved to: {output_path}")

        if pdf:
            from src.analysis import LPAnalysis, ExecutionTimes
            from src.cli import get_system_info
            if not quiet:
                print("Generating PDF report...")
            exec_times = ExecutionTimes(
                parse_time=parse_time,
                build_time=build_time,
                solve_time=solve_time,
                total_time=total_time,
            )
            pdf_path = output or str(input_path.with_suffix('.pdf'))
            system_info = get_system_info()
            analysis = LPAnalysis(problem, solution, exec_times, system_info, solver_name)
            analysis.generate_pdf(pdf_path)
            if not quiet:
                print(f"PDF saved to: {pdf_path}")

        if times and not quiet:
            print("\n" + "=" * 50)
            print("TIEMPOS DE EJECUCION")
            print("=" * 50)
            for label, t in [
                ("Parseo", parse_time),
                ("Construccion LP", build_time),
                (f"Resolucion ({solver_name})", solve_time),
            ]:
                print(f"  {label:<25s} {t * 1000:>10.4f} ms")
            print("-" * 50)
            print(f"  {'TOTAL':<25s} {total_time * 1000:>10.4f} ms")
            print("=" * 50)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def solve_multi(
    input_path: Path,
    solver_name: str = "highs",
    visualize: bool = False,
    pdf: bool = False,
    times: bool = False,
    verbose: bool = False,
    output: Optional[str] = None,
    quiet: bool = False,
    json_output: bool = False,
    time_limit: Optional[float] = None,
) -> int:
    """Resuelve multiples problemas."""
    if not input_path.exists():
        print(f"Error: Archivo no encontrado: {input_path}")
        return 1

    try:
        solver_class = SolverRegistry.get(solver_name)
        if solver_class is None:
            print(f"Error: Solver '{solver_name}' no encontrado")
            return 1

        with open(input_path, 'r') as f:
            content = f.read()

        from src.parser import MultiLPParser
        parser = MultiLPParser(content)
        problems = parser.parse_all()

        if not quiet:
            print(f"\n{'=' * 50}")
            print("MODO MULTI-PROBLEMA")
            print("=" * 50)
            print(f"Problemas encontrados: {len(problems)}")
            print(f"Solver: {solver_name}")
            print()

        results = []
        for i, problem in enumerate(problems, 1):
            if not quiet:
                print(f"--- Problema {i} ---")

            import time
            start = time.perf_counter()

            try:
                config = SolverConfig(verbose=verbose, time_limit=time_limit)
                solver = solver_class(problem, config)
                solution = solver.solve()
                solve_time = time.perf_counter() - start
            except Exception as e:
                if not quiet:
                    print(f"  Error: {e}")
                continue

            from src.solver import ProblemResult
            result = ProblemResult(
                problem=problem,
                solution=solution,
                solve_time=solve_time
            )
            results.append(result)

            if not quiet:
                if solution.is_optimal():
                    print("  Estado: OPTIMAL")
                    print(f"  Valor optimo: {solution.objective_value:.4f}")
                    vars_str = ", ".join(f"{k}={v:.2f}" for k, v in solution.variables.items())
                    print(f"  Variables: {vars_str}")
                else:
                    print(f"  Estado: {solution.status}")

            if visualize and len(problem.variables) == 2:
                from src.visualization import LinearVisualization
                output_name = f"{input_path.stem}_problema_{i}.png"
                viz = LinearVisualization(problem, solution)
                viz.plot(save_path=output_name, show=False)
                if not quiet:
                    print(f"  Grafico guardado: {output_name}")

        if not quiet:
            print(f"\nProblemas resueltos: {len(results)}/{len(problems)}")

        # JSON output for multi
        if json_output:
            import json
            json_results = []
            for r in results:
                json_results.append({
                    "status": r.solution.status,
                    "objective_value": r.solution.objective_value,
                    "variables": r.solution.variables,
                    "solve_time_ms": round(r.solve_time * 1000, 4),
                })
            out = {"solver": solver_name, "problems": json_results}
            print(json.dumps(out, indent=2))

        if pdf and results:
            if not quiet:
                print("Generando reporte PDF multi-problema...")
            try:
                from src.analysis.multi_analysis import MultiLPAnalysis
                from src.solver import MultiSolverResult

                pdf_path = Path(output or input_path.with_stem(input_path.stem + "_multi").with_suffix('.pdf'))
                multi_result = MultiSolverResult(results=results, solver_name=solver_name)
                analysis = MultiLPAnalysis(multi_result)
                analysis.generate_pdf(str(pdf_path))
                if not quiet:
                    print(f"PDF guardado en: {pdf_path}")
            except Exception as e:
                if not quiet:
                    print(f"Error generando PDF multi: {e}")
                if verbose:
                    import traceback
                    traceback.print_exc()

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1
