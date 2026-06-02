"""
Handler para el modo benchmark.
"""

import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from src.parser import MultiLPParser
from src.solver import (
    BenchmarkRunner, BenchmarkConfig
)
from src.analysis import export_benchmark_results
from src.cli import get_system_info
from src.visualization.benchmark_plots import BenchmarkPlotter as BenchmarkVisualizer
from src.report.core.types import ContentType, DocumentModel
from src.report.adapters import ReportData

_console = Console()


def _resolve_template_path(relative: str) -> str:
    """Resolve a template path relative to the report templates directory."""
    base = os.path.join(os.path.dirname(__file__), "..", "report", "templates")
    return os.path.normpath(os.path.join(base, relative))


def _inject_table_data(model: DocumentModel, data: ReportData) -> None:
    """Inject table data from ReportData into DocumentModel elements by element_id."""
    for elem in model.elements:
        if elem.content_type == ContentType.TABLE and elem.element_id in data.tables:
            headers, rows = data.tables[elem.element_id]
            elem.metadata["headers"] = headers
            elem.metadata["rows"] = rows


def _render_report(engine, model, output_path: str, fmt: str, quiet: bool = False, console=None) -> None:
    """Render a document model to the specified format."""
    from src.report.renderers import PDFRenderer, HTMLRenderer, MarkdownRenderer
    from src.report.core.types import RenderContext
    context = RenderContext(
        page_config=model.page_config,
        data=engine._data_binder.data,
        locale=engine._locale_dict,
        current_language=engine.language,
        styles=model.styles,
    )
    renderer_cls = {"pdf": PDFRenderer, "html": HTMLRenderer, "md": MarkdownRenderer}[fmt]
    renderer = renderer_cls(context)
    result = renderer.render(model, output_path)
    if result.success:
        if not quiet:
            console.print(f"[green]{fmt.upper()} saved to:[/green] {output_path}")
    else:
        console.print(f"[red]{fmt.upper()} generation failed:[/red] {'; '.join(result.errors)}")


def run_benchmark(
    input_path: Optional[Path] = None,
    solvers: Optional[list[str]] = None,
    repetitions: int = 1,
    visualize: bool = False,
    output_csv: Optional[str] = None,
    plot_comparison: bool = False,
    output_dir: Optional[str] = None,
    verbose: bool = False,
    report_format: Optional[str] = None,
    quiet: bool = False,
    time_limit: Optional[float] = None,
) -> int:
    """Ejecuta el modo benchmark."""
    solvers = solvers or ['gurobi']
    output_dir_val = Path(output_dir) if output_dir else Path('data/benchmark_output')

    problems = []

    system_info = get_system_info()

    if input_path and input_path.exists():
        with open(input_path, 'r') as f:
            content = f.read()

        if '---' in content:
            parser = MultiLPParser(content)
            parsed_problems = parser.parse_all()
            for i, p in enumerate(parsed_problems, 1):
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
    runner = BenchmarkRunner(config)

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
        runner.run(problems, solvers, on_result=_on_result)

    if not quiet:
        _console.print()
        _console.print(Panel(runner.print_summary(), title="Resumen", border_style="green"))

    if output_csv:
        runner.export_csv(Path(output_csv))
        _console.print(f"\n[green]CSV exported to:[/green] {output_csv}")

    if plot_comparison or visualize:
        _console.print("\n[blue]Generating plots...[/blue]")
        viz = BenchmarkVisualizer(runner)
        viz.generate_all_plots(output_dir_val)
        _console.print(f"[green]Plots saved to:[/green] {output_dir_val}")

    if report_format:
        if not quiet:
            _console.print(f"\n[blue]Generating {report_format.upper()} report...[/blue]")
        from src.report.adapters import adapt_benchmark
        from src.report.engine import ReportEngine

        output_dir_path = Path(output_dir) if output_dir else Path('data/benchmark_output')
        output_dir_path.mkdir(parents=True, exist_ok=True)
        chart_dir = output_dir_path / ".charts"
        chart_dir.mkdir(parents=True, exist_ok=True)

        # Pre-generate charts for the report
        try:
            viz = BenchmarkVisualizer(runner)
            viz.generate_all_plots(chart_dir)
        except Exception:
            if not quiet:
                _console.print("[yellow]Warning: chart generation failed, continuing without charts[/yellow]")

        data = adapt_benchmark(runner, system_info, chart_dir)

        engine = ReportEngine(
            language="es",
            locale_dir=_resolve_template_path("locales"),
            theme_dir=_resolve_template_path("apa"),
        )
        engine.load_csv(_resolve_template_path("apa/benchmark_report.csv"))
        engine.set_variables(data.variables)
        model = engine.build_document_model()
        _inject_table_data(model, data)

        ext = f".{report_format}" if report_format != "md" else ".md"
        fmt_path = output_dir_path / f"report{ext}"
        _render_report(engine, model, str(fmt_path), report_format, quiet, _console)

    export_benchmark_results(runner, output_dir_val, formats=['json', 'csv', 'md'])
    _console.print(f"\n[green]Full results saved to:[/green] {output_dir_val}")

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
