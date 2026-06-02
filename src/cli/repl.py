"""
Modo REPL interactivo para exploracion y resolucion de problemas de PL.
Soporta multiproblemas y benchmark.
"""

import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table

from src.core import LinearProblem
from src.parser import LPParser, MPSParser, MultiLPParser
from src.solver import SolverConfig, SolverRegistry

_console = Console()


def _print_help() -> None:
    """Muestra la ayuda del REPL."""
    table = Table(title="Comandos REPL")
    table.add_column("Comando", style="cyan")
    table.add_column("Descripcion", style="green")
    table.add_column("Ejemplo")
    table.add_row("help", "Muestra esta ayuda", "help")
    table.add_row("load", "Carga un problema desde archivo", "load problema.lp")
    table.add_row("load-mps", "Carga un problema MPS", "load-mps prob.mps")
    table.add_row("load-multi", "Carga multiples problemas", "load-multi multi.txt")
    table.add_row("problems", "Lista problemas cargados", "problems")
    table.add_row("select", "Selecciona un problema por indice", "select 2")
    table.add_row("info", "Muestra informacion del problema", "info")
    table.add_row("solve", "Resuelve con un solver", "solve gurobi")
    table.add_row("benchmark", "Ejecuta benchmark sobre todos", "benchmark")
    table.add_row("solvers", "Lista solvers disponibles", "solvers")
    table.add_row("vars", "Muestra las variables", "vars")
    table.add_row("export", "Exporta a formato LP", "export salida.lp")
    table.add_row("quit", "Sale del REPL", "quit")
    _console.print(table)


def run_repl() -> int:
    """
    Inicia el bucle REPL interactivo.

    Returns:
        0 si termina correctamente.
    """
    _console.print(Panel.fit(
        "[bold yellow]ISLA LP Benchmark REPL[/bold yellow]\n"
        "Escribe [cyan]help[/cyan] para ver los comandos disponibles.\n"
        "Escribe [cyan]quit[/cyan] o Ctrl+C para salir.",
        border_style="yellow",
    ))

    problems: list[LinearProblem] = []
    current_index: int = -1

    def current_problem() -> LinearProblem | None:
        return problems[current_index] if 0 <= current_index < len(problems) else None

    while True:
        try:
            cmd_line = Prompt.ask("[bold cyan]isla>[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            _console.print("\n[bold]Saliendo...[/bold]")
            break

        if not cmd_line:
            continue

        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            break
        elif cmd == "help":
            _print_help()
        elif cmd == "load":
            p = _cmd_load(arg)
            if p is not None:
                problems.append(p)
                current_index = len(problems) - 1
        elif cmd == "load-mps":
            p = _cmd_load_mps(arg)
            if p is not None:
                problems.append(p)
                current_index = len(problems) - 1
        elif cmd == "load-multi":
            loaded = _cmd_load_multi(arg)
            if loaded:
                problems.extend(loaded)
                current_index = len(problems) - 1
        elif cmd == "problems":
            _cmd_problems(problems, current_index)
        elif cmd == "select":
            new_idx = _cmd_select(arg, len(problems))
            if new_idx is not None:
                current_index = new_idx
        elif cmd == "info":
            _cmd_info(current_problem())
        elif cmd == "solve":
            _cmd_solve_repl(problems, current_index, arg)
        elif cmd == "benchmark":
            _cmd_benchmark(problems)
        elif cmd == "solvers":
            _cmd_solvers()
        elif cmd == "vars":
            _cmd_vars(current_problem())
        elif cmd == "export":
            _cmd_export(current_problem(), arg)
        else:
            _console.print(f"[red]Comando desconocido:[/red] {cmd}. Escribe [cyan]help[/cyan] para ayuda.")

    return 0


def _cmd_load(arg: str) -> LinearProblem | None:
    """Carga un problema LP."""
    if not arg:
        _console.print("[red]Uso:[/red] load <archivo>")
        return None
    path = Path(arg)
    if not path.exists():
        _console.print(f"[red]Archivo no encontrado:[/red] {path}")
        return None
    try:
        content = path.read_text()
        problem = LPParser(content).parse()
        _console.print(Panel(
            f"Variables: [bold]{len(problem.variables)}[/bold]\n"
            f"Restricciones: [bold]{len(problem.constraints)}[/bold]\n"
            f"Tipo: [bold]{problem.sense}[/bold]",
            title=f"Problema cargado: {path.name}",
            border_style="green",
        ))
        return problem
    except Exception as e:
        _console.print(f"[red]Error al cargar:[/red] {e}")
        return None


def _cmd_load_mps(arg: str) -> LinearProblem | None:
    """Carga un problema MPS."""
    if not arg:
        _console.print("[red]Uso:[/red] load-mps <archivo>")
        return None
    path = Path(arg)
    if not path.exists():
        _console.print(f"[red]Archivo no encontrado:[/red] {path}")
        return None
    try:
        content = path.read_text()
        problem = MPSParser(content).parse()
        _console.print(Panel(
            f"Variables: [bold]{len(problem.variables)}[/bold]\n"
            f"Restricciones: [bold]{len(problem.constraints)}[/bold]\n"
            f"Tipo: [bold]{problem.sense}[/bold]",
            title=f"Problema MPS cargado: {path.name}",
            border_style="green",
        ))
        return problem
    except Exception as e:
        _console.print(f"[red]Error al cargar MPS:[/red] {e}")
        return None


def _cmd_load_multi(arg: str) -> list[LinearProblem]:
    """Carga multiples problemas desde un archivo multi-formato."""
    if not arg:
        _console.print("[red]Uso:[/red] load-multi <archivo>")
        return []
    path = Path(arg)
    if not path.exists():
        _console.print(f"[red]Archivo no encontrado:[/red] {path}")
        return []
    try:
        content = path.read_text()
        parser = MultiLPParser(content)
        parsed = parser.parse_all()
        if not parsed:
            _console.print("[red]No se encontraron problemas en el archivo.[/red]")
            return []
        _console.print(Panel(
            f"Problemas cargados: [bold]{len(parsed)}[/bold]",
            title=f"Multi-problema: {path.name}",
            border_style="green",
        ))
        return parsed
    except Exception as e:
        _console.print(f"[red]Error al cargar multi-problema:[/red] {e}")
        return []


def _cmd_problems(problems: list[LinearProblem], current_index: int) -> None:
    """Lista los problemas cargados."""
    if not problems:
        _console.print("[yellow]No hay problemas cargados. Usa [cyan]load[/cyan] primero.[/yellow]")
        return
    table = Table(title=f"Problemas ({len(problems)})")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Nombre", style="green")
    table.add_column("Sentido", justify="center")
    table.add_column("Variables", justify="right")
    table.add_column("Restricciones", justify="right")
    table.add_column("Tipo")
    for i, p in enumerate(problems):
        marker = ">" if i == current_index else " "
        name = getattr(p, 'name', '') or f"Problema_{i+1}"
        mip = "MILP" if p.is_mip else "LP"
        table.add_row(f"{marker} {i+1}", name, p.sense, str(len(p.variables)), str(len(p.constraints)), mip)
    _console.print(table)


def _cmd_select(arg: str, n_problems: int) -> int | None:
    """Selecciona un problema por indice."""
    if not arg or not arg.isdigit():
        _console.print("[red]Uso:[/red] select <indice>")
        return None
    idx = int(arg) - 1
    if 0 <= idx < n_problems:
        _console.print(f"[green]Problema {int(arg)} seleccionado.[/green]")
        return idx
    _console.print(f"[red]Indice invalido. Hay {n_problems} problemas.[/red]")
    return None


def _cmd_benchmark(problems: list[LinearProblem]) -> None:
    """Ejecuta benchmark sobre todos los problemas cargados."""
    if not problems:
        _console.print("[yellow]No hay problemas cargados.[/yellow]")
        return
    from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

    from src.solver import BenchmarkConfig, BenchmarkRunner

    problem_tuples = []
    for i, p in enumerate(problems):
        name = getattr(p, 'name', '') or f"Problema_{i+1}"
        problem_tuples.append((name, _problem_to_repl_text(p)))

    solvers = SolverRegistry.list_solvers()
    total = len(problem_tuples) * len(solvers)
    _console.print(f"[blue]Ejecutando benchmark: {len(problem_tuples)} problemas x {len(solvers)} solvers = {total} ejecuciones[/blue]")

    config = BenchmarkConfig(verbose=False)
    runner = BenchmarkRunner(config)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=_console,
    ) as progress:
        task = progress.add_task("Benchmark REPL...", total=total)
        runner.run(problem_tuples, solvers, on_result=lambda _: progress.update(task, advance=1))

    _console.print()
    _console.print(Panel(runner.print_summary(), title="Resultados Benchmark", border_style="green"))


def _problem_to_repl_text(problem: LinearProblem) -> str:
    """Convierte un LinearProblem a texto LP simple."""
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


def _cmd_info(problem: LinearProblem | None) -> None:
    """Muestra informacion del problema."""
    if problem is None:
        _console.print("[yellow]No hay problema cargado. Usa [cyan]load[/cyan] primero.[/yellow]")
        return
    table = Table(title="Informacion del Problema")
    table.add_column("Atributo", style="cyan")
    table.add_column("Valor", style="green")
    table.add_row("Variables", str(len(problem.variables)))
    table.add_row("Restricciones", str(len(problem.constraints)))
    table.add_row("Sentido", problem.sense)
    table.add_row("Es MILP", "Si" if problem.is_mip else "No")
    n_coeffs = sum(len(c.coefficients) for c in problem.constraints)
    table.add_row("Coeficientes totales", str(n_coeffs))
    n_int = sum(1 for v in problem.variable_types.values() if v == "integer")
    table.add_row("Variables enteras", str(n_int))
    n_bin = sum(1 for v in problem.variable_types.values() if v == "binary")
    table.add_row("Variables binarias", str(n_bin))
    _console.print(table)

    obj_expr = " + ".join(f"{c} {v}" for v, c in problem.objective.items())
    _console.print(Syntax(
        f"{problem.sense}: {obj_expr}",
        "text",
        theme="monokai",
    ))


def _cmd_solve_repl(problems: list[LinearProblem], current_index: int, arg: str) -> None:
    """Resuelve un problema con un solver. arg puede ser 'solver' o 'solver idx' o 'idx'."""
    if not problems:
        _console.print("[yellow]No hay problemas cargados. Usa [cyan]load[/cyan] primero.[/yellow]")
        return

    parts = arg.split()
    solver_name = "highs"
    problem = None

    if len(parts) == 0:
        problem = problems[current_index] if 0 <= current_index < len(problems) else problems[-1]
    elif len(parts) == 1:
        if parts[0].isdigit():
            idx = int(parts[0]) - 1
            if 0 <= idx < len(problems):
                problem = problems[idx]
            else:
                _console.print("[red]Indice invalido. Usa [cyan]problems[/cyan] para ver indices.[/red]")
                return
        else:
            solver_name = parts[0]
            problem = problems[current_index] if 0 <= current_index < len(problems) else problems[-1]
    else:
        solver_name = parts[0]
        if parts[1].isdigit():
            idx = int(parts[1]) - 1
            if 0 <= idx < len(problems):
                problem = problems[idx]
            else:
                _console.print("[red]Indice invalido.[/red]")
                return
        else:
            _console.print("[red]Uso: solve [solver] [indice][/red]")
            return

    _solve_problem(problem, solver_name)


def _solve_problem(problem: LinearProblem, solver_name: str) -> None:
    """Resuelve un problema individual e imprime resultado."""
    solver_class = SolverRegistry.get(solver_name)
    if solver_class is None:
        _console.print(f"[red]Solver '{solver_name}' no encontrado.[/red]")
        return
    try:
        config = SolverConfig(verbose=False)
        solver = solver_class(problem, config)
        start = time.perf_counter()
        solution = solver.solve()
        elapsed = time.perf_counter() - start

        if solution.is_optimal():
            _console.print(Panel(
                f"[bold green]Optimo:[/bold green] {solution.objective_value:.6f}\n"
                f"Tiempo: {elapsed * 1000:.2f} ms",
                title=f"Resultado ({solver_name})",
                border_style="green",
            ))
            var_table = Table(title="Variables")
            var_table.add_column("Variable", style="cyan")
            var_table.add_column("Valor", justify="right", style="green")
            for var, val in solution.variables.items():
                var_table.add_row(var, f"{val:.6f}")
            _console.print(var_table)
        else:
            _console.print(f"[yellow]Status:[/yellow] {solution.status}")
    except Exception as e:
        _console.print(f"[red]Error al resolver:[/red] {e}")


def _cmd_solvers() -> None:
    """Lista los solvers disponibles."""
    from src.solver import SolverRegistry
    all_info = SolverRegistry.list_all_info()
    SolverRegistry.list_solvers(available_only=True)
    table = Table(title="Solvers")
    table.add_column("Solver", style="cyan")
    table.add_column("Estado", justify="center")
    for name, info in all_info.items():
        status = "[green]OK[/green]" if info['available'] else "[red]No[/red]"
        table.add_row(name, status)
    _console.print(table)


def _cmd_vars(problem: LinearProblem | None) -> None:
    """Muestra las variables."""
    if problem is None:
        _console.print("[yellow]No hay problema cargado.[/yellow]")
        return
    table = Table(title="Variables")
    table.add_column("Variable", style="cyan")
    table.add_column("Tipo", style="green")
    table.add_column("Inferior", justify="right")
    table.add_column("Superior", justify="right")
    for var in problem.variables:
        vtype = problem.variable_types.get(var, "continuous")
        bound = problem.bounds.get(var)
        lo = f"{bound.lower}" if bound and bound.lower is not None else "-inf"
        up = f"{bound.upper}" if bound and bound.upper is not None else "+inf"
        table.add_row(var, vtype, lo, up)
    _console.print(table)


def _cmd_export(problem: LinearProblem | None, arg: str) -> None:
    """Exporta a formato LP."""
    if problem is None:
        _console.print("[yellow]No hay problema cargado.[/yellow]")
        return
    if not arg:
        _console.print("[red]Uso:[/red] export <archivo>")
        return
    from src.utils.exporter import export_to_lp_file
    try:
        export_to_lp_file(problem, arg)
        _console.print(f"[green]Exportado a:[/green] {arg}")
    except Exception as e:
        _console.print(f"[red]Error al exportar:[/red] {e}")
