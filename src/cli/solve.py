"""
Handler para resolver problemas individuales de programacion lineal.
"""

import os
import time
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.parser import LPParser
from src.solver import SolverConfig, SolverRegistry
from src.visualization import LinearVisualization
from src.report.core.types import ContentType, DocumentModel, ReportElement
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


def _build_report_engine(language: str = "es") -> Any:
    """Create a ReportEngine configured with APA locale and theme."""
    from src.report.engine import ReportEngine
    return ReportEngine(
        language=language,
        locale_dir=_resolve_template_path("locales"),
        theme_dir=_resolve_template_path("apa"),
    )


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


def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    import hashlib
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _build_executive_interpretation(problem, solution, solver_name: str) -> str:
    """Build executive interpretation text."""
    if not solution.is_optimal() or solution.objective_value is None:
        return (
            f"El problema no pudo resolverse de forma optima con el solver {solver_name}. "
            f"Estado final: {solution.status}. Se recomienda revisar las restricciones "
            f"del modelo o probar con otro solver."
        )
    obj_val = solution.objective_value
    direction = "maximizar" if problem.sense.lower() == "max" else "minimizar"
    var_desc = ", ".join(
        f"{k} = {v:.2f}" for k, v in sorted(solution.variables.items())
    )
    return (
        f"Para {direction} la funcion objetivo Z, obteniendo un valor optimo de "
        f"Z* = {obj_val:.4f}, las variables de decision deben tomar los siguientes valores: "
        f"{var_desc}. Esta configuracion satisface todas las restricciones del modelo. "
        f"Desde una perspectiva de negocio, esta solucion representa la asignacion "
        f"mas eficiente de los recursos disponibles bajo las condiciones establecidas."
    )


def solve_single(
    input_path: Path,
    solver_name: str = "highs",
    visualize: bool = False,
    report_format: Optional[str] = None,
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

        problem_hash = _compute_file_hash(input_path)

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

        if report_format:
            from src.analysis.analysis import ExecutionTimes
            from src.report.adapters import adapt_single_solution
            from src.cli import get_system_info
            if not quiet:
                _console.print(f"[blue]Generating {report_format.upper()} report...[/blue]")
            exec_times = ExecutionTimes(
                parse_time=parse_time,
                build_time=build_time,
                solve_time=solve_time,
                total_time=total_time,
            )
            ext = f".{report_format}" if report_format != "md" else ".md"
            fmt_path = output or str(Path(input_path).parent / f"report{ext}")
            system_info = get_system_info()
            system_info["problem_name"] = str(input_path.name)
            system_info["input_format"] = input_path.suffix

            feasible_path = None
            objective_path = None
            if len(problem.variables) == 2 and solution.is_optimal():
                chart_dir = Path(fmt_path).parent / ".charts"
                chart_dir.mkdir(parents=True, exist_ok=True)
                feasible_path = str(chart_dir / "feasible_region.png")
                objective_path = str(chart_dir / "objective_progression.png")
                try:
                    viz = LinearVisualization(problem, solution)
                    viz.plot(save_path=feasible_path, show=False)
                except Exception:
                    feasible_path = None

            solver_config_dict = {
                "time_limit": time_limit,
                "verbose": verbose,
            }
            solver_log = None
            try:
                solver_log = getattr(solver, '_log', None) or str(getattr(solver, 'stats', ''))
            except Exception:
                pass

            exec_interp = _build_executive_interpretation(problem, solution, solver_name)

            # Build semantic problem description
            _p_type = "MILP" if any(
                t in ("integer", "binary") for t in problem.variable_types.values()
            ) else "LP"
            sense_desc = "maximizar" if problem.sense.lower() == "max" else "minimizar"
            var_names = ", ".join(problem.variables)
            problem_description = (
                f"Problema de Programacion Lineal para {sense_desc} una funcion objetivo "
                f"sujeta a {len(problem.constraints)} restricciones. "
                f"Variables de decision: {var_names}. "
                f"Tipo: {_p_type}. "
                "El modelo busca la asignacion optima de recursos limitados para "
                f"{sense_desc} el beneficio total representado por la funcion objetivo."
            )

            data = adapt_single_solution(
                problem, solution, exec_times, system_info, solver_name,
                solver_config=solver_config_dict,
                feasible_region_path=feasible_path,
                objective_progression_path=objective_path,
                solver_log=solver_log,
                problem_file_hash=problem_hash,
                executive_interpretation=exec_interp,
                problem_description=problem_description,
            )
            engine = _build_report_engine()
            engine.load_csv(_resolve_template_path("apa/single_report.csv"))
            engine.set_variables(data.variables)
            model = engine.build_document_model()
            _inject_table_data(model, data)
            _render_report(engine, model, fmt_path, report_format, quiet, _console)

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
    report_format: Optional[str] = None,
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

        if report_format and results:
            if not quiet:
                _console.print(f"[blue]Generando reporte {report_format.upper()} multi-problema...[/blue]")
            try:
                from src.report.adapters import adapt_multi_problem
                from src.cli import get_system_info

                ext = f".{report_format}" if report_format != "md" else ".md"
                fmt_path = Path(output or Path(input_path).parent / f"report_multi{ext}")

                # Generate bar chart of solve times
                chart_path = None
                try:
                    import matplotlib
                    matplotlib.use('Agg')
                    import matplotlib.pyplot as plt
                    chart_dir = Path(fmt_path).parent / ".charts_multi"
                    chart_dir.mkdir(parents=True, exist_ok=True)
                    chart_file = chart_dir / "tiempos_multi.png"

                    labels = [f"P{i+1}" for i in range(len(results))]
                    times = [r.solve_time * 1000 for r in results]
                    colors = ['#e74c3c' if t == max(times) and len(times) > 2 else '#3498db' for t in times]

                    fig, ax = plt.subplots(figsize=(8, 4))
                    bars = ax.bar(labels, times, color=colors, edgecolor='white')
                    ax.set_ylabel("Tiempo (ms)")
                    ax.set_xlabel("Problema")
                    ax.set_title("Tiempo de Resolucion por Problema")
                    ax.axhline(y=sum(times)/len(times), color='gray', linestyle='--', linewidth=0.8, label=f"Media: {sum(times)/len(times):.2f}ms")
                    ax.legend()

                    for bar, t in zip(bars, times):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                                f"{t:.1f}", ha='center', va='bottom', fontsize=7)

                    plt.tight_layout()
                    plt.savefig(str(chart_file), dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    chart_path = str(chart_file)
                except Exception:
                    chart_path = None

                system_info = get_system_info()
                data = adapt_multi_problem(results, solver_name, system_info=system_info, chart_path=chart_path)

                engine = _build_report_engine()
                engine.load_csv(_resolve_template_path("apa/multi_report.csv"))
                engine.set_variables(data.variables)
                model = engine.build_document_model()
                _inject_table_data(model, data)

                # Add per-problem sections programmatically
                _add_problem_sections(model, results)

                _render_report(engine, model, str(fmt_path), report_format, quiet, _console)
            except Exception as e:
                if not quiet:
                    _console.print(f"[red]Error generando reporte {report_format.upper()} multi:[/red] {e}")
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


def _add_problem_sections(model: DocumentModel, results: list) -> None:
    """Add per-problem sections to the document model for multi-problem reports."""
    order = 1000
    for i, r in enumerate(results, 1):
        model.add_element(ReportElement(
            element_id=f"problem_{i}_page_break",
            content_type=ContentType.PAGE_BREAK,
            content="",
            style="default",
            order=order,
        ))
        order += 1

        obj_text = _format_objective_short(r.problem.objective)
        title = f"{r.problem.sense.upper()} Z = {obj_text}"
        model.add_element(ReportElement(
            element_id=f"problem_{i}_title",
            content_type=ContentType.HEADING,
            content=f"Problema {i}: {title}",
            style="apa_subheading",
            order=order,
        ))
        order += 1

        obj_val = r.solution.objective_value
        obj_str = f"{obj_val:.4f}" if obj_val is not None else "N/A"
        n_vars = len(r.problem.variables)
        n_cons = len(r.problem.constraints)
        model.add_element(ReportElement(
            element_id=f"problem_{i}_status",
            content_type=ContentType.PARAGRAPH,
            content=f"Estado: {r.solution.status} | "
                    f"Valor optimo: {obj_str} | "
                    f"Tiempo: {r.solve_time:.4f}s | "
                    f"Dimension: {n_vars} vars, {n_cons} restricciones",
            style="apa_body",
            order=order,
        ))
        order += 1

        var_str = ", ".join(f"{k}={v:.2f}" for k, v in r.solution.variables.items())
        model.add_element(ReportElement(
            element_id=f"problem_{i}_vars",
            content_type=ContentType.PARAGRAPH,
            content=f"Solucion: {var_str}",
            style="apa_body",
            order=order,
        ))
        order += 1

        # Warnings for negative variables
        has_neg = any(v < -1e-6 for v in r.solution.variables.values())
        if has_neg:
            neg_vars = [(k, v) for k, v in r.solution.variables.items() if v < -1e-6]
            neg_desc = "; ".join(f"{k} = {v:.2f}" for k, v in neg_vars)
            model.add_element(ReportElement(
                element_id=f"problem_{i}_neg_warning",
                content_type=ContentType.PARAGRAPH,
                content=f"Alerta de modelado: Las variables {neg_desc} toman valores negativos. "
                        "En LP estandar se asume no negatividad. Esto indica que el modelo "
                        "original define estas variables como libres (free).",
                style="apa_body",
                order=order,
            ))
            order += 1


def _format_objective_short(objective: dict[str, float]) -> str:
    """Format objective coefficients in short form for headings."""
    terms = []
    for var, coeff in objective.items():
        if coeff == 1.0:
            terms.append(f"+{var}")
        elif coeff == -1.0:
            terms.append(f"-{var}")
        else:
            coeff_str = str(int(coeff)) if coeff == int(coeff) else str(coeff)
            if coeff >= 0:
                terms.append(f"+{coeff_str}{var}")
            else:
                terms.append(f"{coeff_str}{var}")
    expr = " ".join(terms)
    if expr.startswith("+"):
        expr = expr[1:]
    return expr
