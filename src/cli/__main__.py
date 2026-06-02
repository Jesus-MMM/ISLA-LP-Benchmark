"""
Modulo de CLI para el solver de programacion lineal.
Maneja la interfaz de linea de comandos.
"""

import argparse
import sys
from pathlib import Path
from typing import TextIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_console = Console()


class CustomHelpFormatter(
    argparse.RawDescriptionHelpFormatter,
    argparse.ArgumentDefaultsHelpFormatter,
):
    """Personaliza la salida de ayuda de argparse combinando la preservación de saltos de línea
    con la muestra de valores por defecto."""


def _version() -> str:
    """Retorna la version del paquete."""
    try:
        from importlib.metadata import version
        return version("isla-lp-benchmark")
    except Exception:
        return "1.8.1"


def _install_completion() -> int:
    """Instala autocompletado para bash/zsh."""
    completion_script = f"""_{Path(sys.argv[0]).name}() {{
    local cur opts
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    opts="--version -V --list-solvers -l --log-level --solver -s --solvers -S --all-solvers -a --timeout -T --multi -m --visualize -v --pdf -p --times -t --no-solve -n --benchmark -b --repetitions -r --plot-comparison -C --output-csv --output -o --output-dir -O --json -j --quiet -q --verbose --help -h --install-completion input"
    COMPREPLY=($(compgen -W "${{opts}}" -- "${{cur}}"))
    return 0
}}
complete -F _Path(sys.argv[0])name {Path(sys.argv[0]).name}"""
    completion_path = Path("~/.local/share/isla-lp-benchmark/completion.sh").expanduser()
    completion_path.parent.mkdir(parents=True, exist_ok=True)
    completion_path.write_text(completion_script)
    _console.print(f"[green]Autocompletado instalado en:[/green] {completion_path}")
    _console.print("[yellow]Agrega la siguiente linea a tu ~/.bashrc o ~/.zshrc:[/yellow]")
    _console.print(f"  [bold]source {completion_path}[/bold]")
    return 0


class _RichArgumentParser(argparse.ArgumentParser):
    """Parser que muestra la ayuda con secciones en paneles Rich."""

    def print_help(self, file: TextIO | None = None) -> None:
        """Imprime la ayuda formateada con paneles de Rich."""
        text = argparse.ArgumentParser.format_help(self)
        lines = text.split('\n')
        sections = []
        current_section = {"title": None, "body": []}
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_section["body"]:
                    sections.append(current_section)
                    current_section = {"title": None, "body": []}
            elif current_section["title"] is None:
                if stripped.lower().startswith('usage:'):
                    current_section["title"] = "usage"
                    current_section["body"].append(stripped)
                elif stripped == '':
                    continue
                else:
                    current_section["title"] = stripped.rstrip(':')
                    current_section["body"] = []
            else:
                current_section["body"].append(line)
        if current_section["body"] or current_section["title"] is not None:
            sections.append(current_section)

        panels = []
        for sec in sections:
            title = sec["title"]
            if title == "usage":
                usage_panel = Panel(
                    sec['body'][0],
                    title="[bold yellow]Uso[/bold yellow]",
                    border_style="yellow",
                )
                panels.append(usage_panel)
            elif title:
                body_lines = []
                for ln in sec["body"]:
                    stripped = ln.strip()
                    if stripped.startswith('-') or stripped.startswith('  -'):
                        parts = ln.split('  ', 1)
                        if len(parts) == 2 and parts[1].strip():
                            body_lines.append(f"  [green]{parts[0].strip()}[/green]    {parts[1].strip()}")
                        else:
                            body_lines.append(f"  [green]{stripped}[/green]")
                    else:
                        body_lines.append(ln)
                body_text = '\n'.join(body_lines) if body_lines else "[dim]—[/dim]"
                sec_panel = Panel(
                    body_text,
                    title=f"[bold cyan]{title}[/bold cyan]",
                    border_style="cyan",
                )
                panels.append(sec_panel)

        from rich.console import Group
        _console.print(Panel(
            Group(*panels),
            title="[bold]ISLA LP Solver[/bold]",
            border_style="bright_blue",
        ))

    def format_help(self) -> str:
        """Retorna el texto de ayuda estándar de argparse."""
        return argparse.ArgumentParser.format_help(self)


def create_parser() -> argparse.ArgumentParser:
    """Crea el parser de argumentos con secciones organizadas."""
    parser = _RichArgumentParser(
        prog='isla',
        description='Solucionador de Programacion Lineal - Soporta LP/MILP con Gurobi y otros motores',
        formatter_class=CustomHelpFormatter,
        epilog="""\
Ejemplos de uso
---------------

  Resolver un problema:
    %(prog)s problema.txt
    %(prog)s problema.txt -s cbc
    %(prog)s problema.txt -s highs -v -p -t
    %(prog)s problema.txt -T 30                   (timeout 30s)
    %(prog)s problema.txt -P mps                   (formato MPS)
    %(prog)s problema.txt -P cplex                 (formato LP/CPLEX)

  Multi-problema (separador --- en el archivo):
    %(prog)s problema.txt -m
    %(prog)s problema.txt -m -p

  Benchmark:
    %(prog)s --benchmark problemas.txt
    %(prog)s -b problemas.txt -a
    %(prog)s -b problemas.txt -S cbc glpk -r 5
    %(prog)s -b problemas.txt -a -C
    %(prog)s -b problema.mps -P mps                (benchmark con MPS)
    %(prog)s -b problemas.txt --parallel           (benchmark paralelo)

  Salida estructurada:
    %(prog)s problema.txt -j                (JSON a stdout)
    %(prog)s problema.txt -j -o salida.json

  Solo parsear (diagnostico):
    %(prog)s problema.txt -n
    %(prog)s problema.mps -n -P mps                (parsear MPS)

  Informacion:
    %(prog)s --list-solvers
    %(prog)s --version

Para mas ayuda sobre un modo concreto, combine las opciones:
  %(prog)s -b --help       (opciones de benchmark)
  %(prog)s -v -p --help    (opciones de visualizacion)
        """
    )

    # --- Posicional ---
    parser.add_argument(
        'input',
        nargs='?',
        help='Archivo con el problema de PL (LP, CPLEX LP o MPS)'
    )

    # --- General / Informacion ---
    info_group = parser.add_argument_group('Informacion')
    class _RichVersionAction(argparse.Action):
        def __init__(self, option_strings, dest, version=None, **kwargs):
            self.version = version
            super().__init__(option_strings, dest, nargs=0, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            _print_banner()
            _console.print(f"[bold cyan]isla[/bold cyan] [green]{self.version}[/green]")
            parser.exit()

    info_group.add_argument(
        '--version', '-V',
        action=_RichVersionAction,
        version=f'{_version()}',
        help='Mostrar la version del programa y salir'
    )
    info_group.add_argument(
        '--list-solvers', '-l',
        action='store_true',
        help='Mostrar todos los solvers registrados y su disponibilidad'
    )
    info_group.add_argument(
        '--log-level',
        type=str,
        default=None,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Nivel de detalle de los mensajes de registro (default: WARNING)'
    )
    info_group.add_argument(
        '--install-completion',
        action='store_true',
        help='Instalar autocompletado para bash/zsh'
    )
    info_group.add_argument(
        '--repl',
        action='store_true',
        help='Iniciar modo REPL interactivo'
    )

    # --- Seleccion de parser ---
    parser_group = parser.add_argument_group('Seleccion de parser')
    parser_group.add_argument(
        '--parser', '-P',
        type=str,
        default='auto',
        choices=['auto', 'lp', 'cplex', 'mps'],
        help='Formato del archivo de entrada: auto (detecta por extension/contenido), lp (libre), cplex (CPLEX LP), mps (MPS)'
    )

    # --- Seleccion de solver ---
    solver_group = parser.add_argument_group('Seleccion de solver')
    solver_group.add_argument(
        '--solver', '-s',
        type=str,
        default='gurobi',
        help='Nombre del solver a utilizar'
    )
    solver_group.add_argument(
        '--solvers', '-S',
        nargs='+',
        default=['gurobi'],
        metavar='SOLVER',
        help='Lista de solvers a comparar en el benchmark (separados por espacio)'
    )
    solver_group.add_argument(
        '--all-solvers', '-a',
        action='store_true',
        help='Usar automaticamente todos los solvers disponibles detectados en el sistema'
    )
    solver_group.add_argument(
        '--timeout', '-T',
        type=float,
        default=None,
        metavar='SEG',
        help='Limite de tiempo por solver en segundos (timeout)'
    )

    # --- Modo resolver ---
    solve_group = parser.add_argument_group('Opciones de resolucion')
    solve_group.add_argument(
        '--multi', '-m',
        action='store_true',
        help='Activar modo multi-problema (problemas separados por --- en el archivo de entrada)'
    )
    solve_group.add_argument(
        '--visualize', '-v',
        action='store_true',
        help='Generar grafica de la region factible (solo problemas 2D)'
    )
    solve_group.add_argument(
        '--pdf', '-p',
        action='store_true',
        help='Generar reporte PDF con el analisis completo de la solucion'
    )
    solve_group.add_argument(
        '--times', '-t',
        action='store_true',
        help='Mostrar desglose de tiempos de ejecucion (parseo, construccion, resolucion)'
    )
    solve_group.add_argument(
        '--no-solve', '-n',
        action='store_true',
        help='Solo parsear y mostrar el problema, sin resolver'
    )

    # --- Modo benchmark ---
    bench_group = parser.add_argument_group('Opciones de benchmark')
    bench_group.add_argument(
        '--benchmark', '-b',
        action='store_true',
        help='Ejecutar en modo benchmark: evalua multiples solvers sobre uno o varios problemas'
    )
    bench_group.add_argument(
        '--repetitions', '-r',
        type=int,
        default=1,
        metavar='N',
        help='Numero de repeticiones por problema para obtener mediciones estadisticas'
    )
    bench_group.add_argument(
        '--plot-comparison', '-C',
        action='store_true',
        help='Generar graficos comparativos de rendimiento entre solvers'
    )
    bench_group.add_argument(
        '--output-csv',
        type=str,
        metavar='ARCHIVO',
        help='Exportar resultados del benchmark a un archivo CSV'
    )
    bench_group.add_argument(
        '--parallel',
        action='store_true',
        help='Ejecutar benchmark en procesos paralelos aislados (evita interferencias entre solvers)'
    )

    # --- Salida ---
    output_group = parser.add_argument_group('Opciones de salida')
    output_group.add_argument(
        '--format',
        type=str,
        choices=['pdf', 'html', 'md'],
        default=None,
        metavar='FORMATO',
        help='Formato del reporte (pdf, html, md). Por defecto no se genera reporte, usar --pdf o --format'
    )
    output_group.add_argument(
        '--output', '-o',
        type=str,
        metavar='RUTA',
        help='Ruta de salida para archivos generados (graficas, PDFs, JSON)'
    )
    output_group.add_argument(
        '--output-dir', '-O',
        type=str,
        metavar='DIR',
        default=None,
        help='Directorio de salida para resultados de benchmark'
    )
    output_group.add_argument(
        '--json', '-j',
        action='store_true',
        help='Mostrar resultado en formato JSON (salida estructurada)'
    )
    output_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suprimir toda salida no esencial (solo mostrar resultados)'
    )
    output_group.add_argument(
        '--verbose',
        action='store_true',
        help='Mostrar informacion detallada durante la ejecucion (incluye tracebacks de errores)'
    )

    return parser


def _print_banner() -> None:
    """Muestra el banner de bienvenida del CLI."""
    _console.print(Panel.fit(
        "[bold cyan]ISLA LP Benchmark[/bold cyan]\n"
        f"[green]v{_version()}[/green] - Solucionador de Programacion Lineal\n"
        "[dim]Soporta LP/MILP con 10+ motores de optimizacion[/dim]",
        border_style="cyan",
    ))


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada principal."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.log_level is not None:
        from src.utils.logging import LogLevel, set_default_level
        set_default_level(LogLevel[args.log_level])

    if args.install_completion:
        return _install_completion()

    if args.repl:
        from src.cli.repl import run_repl
        return run_repl()

    if args.list_solvers:
        from src.solver import SolverRegistry
        all_info = SolverRegistry.list_all_info()
        available = SolverRegistry.list_solvers(available_only=True)

        _print_banner()
        table = Table(title="Solvers Registrados")
        table.add_column("Solver", style="cyan")
        table.add_column("Estado", justify="center")
        table.add_column("Detalle")

        for name, info in all_info.items():
            if info['available']:
                status = "[green]DISPONIBLE[/green]"
                error = ""
            else:
                status = "[red]NO DISPONIBLE[/red]"
                error = info.get('error', '')
            table.add_row(name, status, error)

        _console.print(table)
        _console.print(f"\n[bold]{len(available)}/{len(all_info)}[/bold] solvers disponibles: [green]{', '.join(available)}[/green]")
        return 0

    solver_name = args.solver

    # Compute effective format: --format overrides --pdf, --pdf sets pdf
    report_format = args.format
    if args.pdf and report_format is None:
        report_format = "pdf"

    if args.benchmark:
        from src.cli.benchmark import run_benchmark
        from src.solver import SolverRegistry
        solvers = args.solvers or ['gurobi']
        if args.all_solvers:
            solvers = SolverRegistry.list_solvers(available_only=True)

        return run_benchmark(
            input_path=Path(args.input) if args.input else None,
            solvers=solvers,
            repetitions=args.repetitions,
            visualize=args.plot_comparison,
            output_csv=args.output_csv,
            plot_comparison=args.plot_comparison,
            output_dir=args.output_dir if args.output_dir else None,
            verbose=args.verbose,
            report_format=report_format,
            quiet=args.quiet,
            time_limit=args.timeout,
            parser_name=args.parser,
            parallel=args.parallel,
        )

    if args.input:
        if args.no_solve:
            return _parse_only(Path(args.input), verbose=args.verbose, parser_name=args.parser)

        kwargs = dict(
            solver_name=solver_name,
            visualize=args.visualize,
            report_format=report_format,
            times=args.times,
            verbose=args.verbose,
            output=args.output,
            quiet=args.quiet,
            json_output=args.json,
            time_limit=args.timeout,
            parser_name=args.parser,
        )

        if args.multi:
            from src.cli.solve import solve_multi
            return solve_multi(Path(args.input), **kwargs)
        else:
            from src.cli.solve import solve_single
            return solve_single(Path(args.input), **kwargs)

    _print_banner()
    parser.print_help()
    return 0


def _parse_only(path: Path, verbose: bool = False, parser_name: str = "auto") -> int:
    """Solo parsea y muestra informacion del problema sin resolver."""
    if not path.exists():
        _console.print(f"[red]Error:[/red] Archivo no encontrado: {path}")
        return 1

    try:
        with open(path) as f:
            content = f.read()

        from src.matrix import LPBuilder
        from src.parser import get_parser_class

        parser_cls = get_parser_class(parser_name, content, path.suffix)

        if '---' in content:
            import re
            sections = re.split(r'(?:---+|===+|___+)\s*\n', content)
            sections = [s.strip() for s in sections if s.strip()]
            problems = [parser_cls(s).parse() for s in sections]
            _console.print(Panel(
                f"[bold cyan]Problemas encontrados:[/bold cyan] {len(problems)}",
                border_style="blue",
            ))
            for i, p in enumerate(problems, 1):
                tbl = Table(title=f"Problema {i}", show_header=False)
                tbl.add_column("Atributo", style="cyan")
                tbl.add_column("Valor", style="green")
                tbl.add_row("Variables", str(len(p.variables)))
                tbl.add_row("Restricciones", str(len(p.constraints)))
                tbl.add_row("Tipo", p.sense)
                lp = LPBuilder(p).build()
                n_rows = lp.constraints.shape[0] if hasattr(lp, 'constraints') else '?'
                n_cols = lp.objective.shape[0] if hasattr(lp, 'objective') else '?'
                tbl.add_row("Matriz", f"{n_rows}x{n_cols} (Polars LP)")
                _console.print(tbl)
        else:
            problem = parser_cls(content).parse()
            lp = LPBuilder(problem).build()
            tbl = Table(title=f"Problema: {path.name}", show_header=False)
            tbl.add_column("Atributo", style="cyan")
            tbl.add_column("Valor", style="green")
            tbl.add_row("Variables", str(len(problem.variables)))
            tbl.add_row("Restricciones", str(len(problem.constraints)))
            tbl.add_row("Tipo", problem.sense)
            n_rows = lp.constraints.shape[0] if hasattr(lp, 'constraints') else '?'
            n_cols = lp.objective.shape[0] if hasattr(lp, 'objective') else '?'
            tbl.add_row("Matriz", f"{n_rows}x{n_cols} (Polars LP)")
            tbl.add_row("Variables", ", ".join(problem.variables))
            _console.print(tbl)
        return 0
    except Exception as e:
        _console.print(f"[red]Error al parsear:[/red] {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
