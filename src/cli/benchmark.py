"""
Handler para el modo benchmark.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from src.solver import (
    BenchmarkRunner, BenchmarkConfig
)

_console = Console()


def run_benchmark(
    input_path: Optional[Path] = None,
    solvers: Optional[list[str]] = None,
    repetitions: int = 1,
    visualize: bool = False,
    output_csv: Optional[str] = None,
    plot_comparison: bool = False,
    output_dir: Optional[str] = None,
    verbose: bool = False,
    pdf: bool = False,
    quiet: bool = False,
    time_limit: Optional[float] = None,
    parser_name: str = "auto",
    parallel: bool = False,
) -> int:
    """Ejecuta el modo benchmark."""
    solvers = solvers or ['gurobi']
    output_dir_val = Path(output_dir) if output_dir else Path('data/benchmark_output')

    problems = []

    from src.cli import get_system_info
    system_info = get_system_info()

    if input_path and input_path.exists():
        with open(input_path, 'r') as f:
            content = f.read()

        if '---' in content:
            import re
            from src.parser import get_parser_class
            parser_cls = get_parser_class(parser_name, content, input_path.suffix)
            sections = re.split(r'(?:---+|===+|___+)\s*\n', content)
            for i, section in enumerate([s.strip() for s in sections if s.strip()], 1):
                p = parser_cls(section).parse()
                problems.append((f"Problema_{i}", _problem_to_text(p)))
        else:
            problems.append((input_path.stem, content))
    else:
        problems = [
            ("Problema_1", "max Z = x + y\nx + y <= 10\nx >= 0\ny >= 0"),
            ("Problema_2", "max Z = 3x + 5y\n2x + y <= 18\nx + 3y <= 24\nx >= 0\ny >= 0"),
            ("Problema_3", "min Z = 2x + 3y\nx + y >= 5\n2x + y >= 8\nx >= 0\ny >= 0"),
        ]

    if not quiet:
        info_table = Table(title="Benchmark Configuration")
        info_table.add_column("Parametro", style="cyan")
        info_table.add_column("Valor", style="green")
        info_table.add_row("Problems", str(len(problems)))
        info_table.add_row("Solvers", ", ".join(solvers))
        info_table.add_row("Repetitions", str(repetitions))
        info_table.add_row("Output", str(output_dir))
        if time_limit:
            info_table.add_row("Time limit", f"{time_limit}s")
        _console.print(info_table)
        _console.print()

    config = BenchmarkConfig(
        verbose=verbose,
        runs_per_problem=repetitions,
        time_limit=time_limit,
    )

    if parallel:
        from src.solver import ParallelBenchmarkRunner, ParallelBenchmarkConfig
        pconfig = ParallelBenchmarkConfig(
            warmup_runs=0,
            runs_per_problem=repetitions,
            verbose=verbose,
            time_limit=time_limit,
            collect_memory=True,
            collect_solution_table=True,
        )
        runner = ParallelBenchmarkRunner(pconfig, parser_name=parser_name)
        _results = runner.run(problems, solvers, timeout=time_limit or 300)
        # Re-wrap into BenchmarkRunner for downstream compatibility
        runner_wrapper = BenchmarkRunner(config, parser_name=parser_name)
        runner_wrapper.results = _results
        runner = runner_wrapper
    else:
        runner = BenchmarkRunner(config, parser_name=parser_name)

    total_tasks = len(problems) * len(solvers) * repetitions
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=_console,
        disable=quiet,
    ) as progress:
        task = progress.add_task("Running benchmark...", total=total_tasks)
        def _on_result(_result):
            progress.update(task, advance=1)
        if not parallel:
            runner.run(problems, solvers, on_result=_on_result)

    if not quiet:
        _console.print()
        _console.print(Panel(runner.print_summary(), title="Resumen", border_style="green"))

    if output_csv:
        runner.export_csv(Path(output_csv))
        _console.print(f"\n[green]CSV exported to:[/green] {output_csv}")

    if plot_comparison or visualize:
        from src.visualization.benchmark_plots import BenchmarkPlotter as BenchmarkVisualizer
        _console.print("\n[blue]Generating plots...[/blue]")
        viz = BenchmarkVisualizer(runner)
        viz.generate_all_plots(output_dir_val)
        _console.print(f"[green]Plots saved to:[/green] {output_dir_val}")

    if pdf:
        _console.print("\n[blue]Generating PDF report...[/blue]")
        from src.analysis import BenchmarkReport

        output_dir_path = Path(output_dir) if output_dir else Path('data/benchmark_output')
        output_dir_path.mkdir(parents=True, exist_ok=True)

        pdf_path = output_dir_path / "benchmark_report.pdf"
        benchmark_report = BenchmarkReport(runner, system_info)
        benchmark_report.generate(str(pdf_path))
        _console.print(f"[green]PDF saved to:[/green] {pdf_path}")

    from src.analysis import export_benchmark_results
    export_benchmark_results(runner, output_dir_val, formats=['json', 'csv', 'md'])
    _console.print(f"\n[green]Full results saved to:[/green] {output_dir}")

    return 0


def _problem_to_text(problem) -> str:
    """Convierte un LinearProblem a texto."""
    sense = problem.sense.upper()
    terms = []
    for var, coeff in problem.objective.items():
        if coeff >= 0:
            terms.append(f"+{coeff}{var}")
        else:
            terms.append(f"{coeff}{var}")
    obj = " ".join(terms) if terms else "0"
    if obj.startswith("+"):
        obj = obj[1:]
    lines = [f"{sense} Z = {obj}"]
    
    for c in problem.constraints:
        c_terms = []
        for var, coeff in c.coefficients.items():
            if coeff >= 0:
                c_terms.append(f"+{coeff}{var}")
            else:
                c_terms.append(f"{coeff}{var}")
        c_str = " ".join(c_terms)
        if c_str.startswith("+"):
            c_str = c_str[1:]
        lines.append(f"{c_str} {c.sense} {c.rhs}")
    
    for var, bound in problem.bounds.items():
        if bound.lower is not None and bound.upper is not None:
            lines.append(f"{bound.lower} <= {var} <= {bound.upper}")
        elif bound.lower is not None:
            lines.append(f"{var} >= {bound.lower}")
        elif bound.upper is not None:
            lines.append(f"{var} <= {bound.upper}")
    
    return "\n".join(lines)
