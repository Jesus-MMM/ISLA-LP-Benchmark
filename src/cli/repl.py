"""
Modo REPL interactivo para exploracion y resolucion de problemas de PL.
"""

import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt

from src.parser import LPParser, MPSParser
from src.solver import SolverConfig, SolverRegistry
from src.core import LinearProblem

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
    table.add_row("info", "Muestra informacion del problema", "info")
    table.add_row("solve", "Resuelve con un solver", "solve gurobi")
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

    problem: Optional[LinearProblem] = None

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
            problem = _cmd_load(arg)
        elif cmd == "load-mps":
            problem = _cmd_load_mps(arg)
        elif cmd == "info":
            _cmd_info(problem)
        elif cmd == "solve":
            _cmd_solve(problem, arg)
        elif cmd == "solvers":
            _cmd_solvers()
        elif cmd == "vars":
            _cmd_vars(problem)
        elif cmd == "export":
            _cmd_export(problem, arg)
        else:
            _console.print(f"[red]Comando desconocido:[/red] {cmd}. Escribe [cyan]help[/cyan] para ayuda.")

    return 0


def _cmd_load(arg: str) -> Optional[LinearProblem]:
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


def _cmd_load_mps(arg: str) -> Optional[LinearProblem]:
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


def _cmd_info(problem: Optional[LinearProblem]) -> None:
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


def _cmd_solve(problem: Optional[LinearProblem], arg: str) -> None:
    """Resuelve el problema con un solver."""
    if problem is None:
        _console.print("[yellow]No hay problema cargado. Usa [cyan]load[/cyan] primero.[/yellow]")
        return
    solver_name = arg or "highs"
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


def _cmd_vars(problem: Optional[LinearProblem]) -> None:
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


def _cmd_export(problem: Optional[LinearProblem], arg: str) -> None:
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
