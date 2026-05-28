"""
Handler para resolver problemas individuales de programacion lineal.
"""

import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.parser import LPParser
from src.solver import SolverConfig, SolverRegistry
from src.visualization import LinearVisualization


_console = Console()


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
        _console.print(f"[red]Error:[/red] Archivo no encontrado: {input_path}")
        return 1

    start_total = time.perf_counter()

    try:
        solver_class = SolverRegistry.get(solver_name)
        if solver_class is None:
            _console.print(f"[red]Error:[/red] Solver '{solver_name}' no encontrado")
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
                    _console.print(f"[green]JSON saved to:[/green] {output_path}")
            else:
                _console.print(json.dumps(result, indent=2))
            return 0

        # Normal output with Rich
        if not quiet:
            if solution.is_optimal():
                panel = Panel(
                    f"[bold green]Optimal value:[/bold green] {solution.objective_value:.4f}",
                    title="Resultado",
                    border_style="green",
                )
                _console.print(panel)
                var_table = Table(title="Variables")
                var_table.add_column("Variable", style="cyan")
                var_table.add_column("Valor", justify="right", style="green")
                for var, value in solution.variables.items():
                    var_table.add_row(var, f"{value:.4f}")
                _console.print(var_table)
            else:
                _console.print(f"[yellow]Status:[/yellow] {solution.status}")

        if visualize and len(problem.variables) == 2:
            output_path = output or str(input_path.with_suffix('.png'))
            viz = LinearVisualization(problem, solution)
            viz.plot(save_path=str(output_path), show=False)
            if not quiet:
                _console.print(f"[green]Graph saved to:[/green] {output_path}")

        if pdf:
            from src.analysis import LPAnalysis, ExecutionTimes
            from src.cli import get_system_info
            if not quiet:
                _console.print("[blue]Generating PDF report...[/blue]")
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
                _console.print(f"[green]PDF saved to:[/green] {pdf_path}")

        if times and not quiet:
            time_table = Table(title="Tiempos de Ejecucion")
            time_table.add_column("Fase", style="cyan")
            time_table.add_column("Tiempo (ms)", justify="right", style="green")
            for label, t in [
                ("Parseo", parse_time),
                ("Construccion LP", build_time),
                (f"Resolucion ({solver_name})", solve_time),
            ]:
                time_table.add_row(label, f"{t * 1000:.4f}")
            time_table.add_row("[bold]TOTAL[/bold]", f"[bold]{total_time * 1000:.4f}[/bold]")
            _console.print(time_table)

        return 0

    except Exception as e:
        _console.print(f"[red]Error:[/red] {e}")
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
        _console.print(f"[red]Error:[/red] Archivo no encontrado: {input_path}")
        return 1

    try:
        solver_class = SolverRegistry.get(solver_name)
        if solver_class is None:
            _console.print(f"[red]Error:[/red] Solver '{solver_name}' no encontrado")
            return 1

        with open(input_path, 'r') as f:
            content = f.read()

        from src.parser import MultiLPParser
        parser = MultiLPParser(content)
        problems = parser.parse_all()

        if not quiet:
            _console.print(Panel(
                f"Problemas encontrados: [bold]{len(problems)}[/bold]\n"
                f"Solver: [bold]{solver_name}[/bold]",
                title="MODO MULTI-PROBLEMA",
                border_style="blue",
            ))

        results = []
        for i, problem in enumerate(problems, 1):
            if not quiet:
                _console.print(f"\n[bold cyan]--- Problema {i} ---[/bold cyan]")

            import time
            start = time.perf_counter()

            try:
                config = SolverConfig(verbose=verbose, time_limit=time_limit)
                solver = solver_class(problem, config)
                solution = solver.solve()
                solve_time = time.perf_counter() - start
            except Exception as e:
                if not quiet:
                    _console.print(f"  [red]Error:[/red] {e}")
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
                    _console.print("  [green]Estado:[/green] OPTIMAL")
                    _console.print(f"  [green]Valor optimo:[/green] {solution.objective_value:.4f}")
                    vars_str = ", ".join(f"{k}={v:.2f}" for k, v in solution.variables.items())
                    _console.print(f"  Variables: {vars_str}")
                else:
                    _console.print(f"  [yellow]Estado:[/yellow] {solution.status}")

            if visualize and len(problem.variables) == 2:
                from src.visualization import LinearVisualization
                output_name = f"{input_path.stem}_problema_{i}.png"
                viz = LinearVisualization(problem, solution)
                viz.plot(save_path=output_name, show=False)
                if not quiet:
                    _console.print(f"  [green]Grafico guardado:[/green] {output_name}")

        if not quiet:
            _console.print(f"\nProblemas resueltos: [bold]{len(results)}/{len(problems)}[/bold]")

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
            _console.print(json.dumps(out, indent=2))

        if pdf and results:
            if not quiet:
                _console.print("[blue]Generando reporte PDF multi-problema...[/blue]")
            try:
                from src.analysis.multi_analysis import MultiLPAnalysis
                from src.solver import MultiSolverResult

                pdf_path = Path(output or input_path.with_stem(input_path.stem + "_multi").with_suffix('.pdf'))
                multi_result = MultiSolverResult(results=results, solver_name=solver_name)
                analysis = MultiLPAnalysis(multi_result)
                analysis.generate_pdf(str(pdf_path))
                if not quiet:
                    _console.print(f"[green]PDF guardado en:[/green] {pdf_path}")
            except Exception as e:
                if not quiet:
                    _console.print(f"[red]Error generando PDF multi:[/red] {e}")
                if verbose:
                    import traceback
                    traceback.print_exc()

        return 0

    except Exception as e:
        _console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1
