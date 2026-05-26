"""
Modulo de CLI para el solver de programacion lineal.
Maneja la interfaz de linea de comandos.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.cli import solve, benchmark


class CustomHelpFormatter(
    argparse.RawDescriptionHelpFormatter,
    argparse.ArgumentDefaultsHelpFormatter,
):
    """Formateador combinado: preserva saltos de linea + muestra valores por defecto."""


def _version() -> str:
    """Retorna la version del paquete."""
    try:
        from importlib.metadata import version
        return version("isla-lp-benchmark")
    except Exception:
        return "1.2.1"


def create_parser() -> argparse.ArgumentParser:
    """Crea el parser de argumentos con secciones organizadas."""
    parser = argparse.ArgumentParser(
        prog='lp-solver',
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

  Multi-problema (separador --- en el archivo):
    %(prog)s problema.txt -m
    %(prog)s problema.txt -m -p

  Benchmark:
    %(prog)s --benchmark problemas.txt
    %(prog)s -b problemas.txt -a
    %(prog)s -b problemas.txt -S cbc glpk -r 5
    %(prog)s -b problemas.txt -a -C

  Salida estructurada:
    %(prog)s problema.txt -j                (JSON a stdout)
    %(prog)s problema.txt -j -o salida.json

  Solo parsear (diagnostico):
    %(prog)s problema.txt -n

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
        help='Archivo con el problema de PL en formato LP estandar'
    )

    # --- General / Informacion ---
    info_group = parser.add_argument_group('Informacion')
    info_group.add_argument(
        '--version', '-V',
        action='version',
        version=f'%(prog)s {_version()}',
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

    # --- Salida ---
    output_group = parser.add_argument_group('Opciones de salida')
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


def main(argv: Optional[list[str]] = None) -> int:
    """Punto de entrada principal."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Configurar nivel de logging global
    if args.log_level is not None:
        from src.utils.logging import LogLevel, set_default_level
        set_default_level(LogLevel[args.log_level])

    if args.list_solvers:
        from src.solver import SolverRegistry
        all_info = SolverRegistry.list_all_info()
        available = SolverRegistry.list_solvers(available_only=True)

        print()
        print("  Solvers registrados")
        print("  " + "-" * 50)
        for name, info in all_info.items():
            if info['available']:
                status = "  DISPONIBLE"
                error = ""
            else:
                status = "  NO DISPONIBLE"
                error = f"  ({info['error']})" if info['error'] else ""
            print(f"    {name:<20s}{status}{error}")
        print()
        print(f"  {len(available)}/{len(all_info)} solvers disponibles: {', '.join(available)}")
        print()
        return 0

    solver_name = args.solver

    if args.benchmark:
        from src.solver import SolverRegistry
        solvers = args.solvers or ['gurobi']
        if args.all_solvers:
            solvers = SolverRegistry.list_solvers(available_only=True)

        return benchmark.run_benchmark(
            input_path=Path(args.input) if args.input else None,
            solvers=solvers,
            repetitions=args.repetitions,
            visualize=args.plot_comparison,
            output_csv=args.output_csv,
            plot_comparison=args.plot_comparison,
            output_dir=args.output_dir if args.output_dir else None,
            verbose=args.verbose,
            pdf=args.pdf,
            quiet=args.quiet,
            time_limit=args.timeout,
        )

    if args.input:
        if args.no_solve:
            return _parse_only(Path(args.input), verbose=args.verbose)

        kwargs = dict(
            solver_name=solver_name,
            visualize=args.visualize,
            pdf=args.pdf,
            times=args.times,
            verbose=args.verbose,
            output=args.output,
            quiet=args.quiet,
            json_output=args.json,
            time_limit=args.timeout,
        )

        if args.multi:
            return solve.solve_multi(Path(args.input), **kwargs)
        else:
            return solve.solve_single(Path(args.input), **kwargs)

    parser.print_help()
    return 0


def _parse_only(path: Path, verbose: bool = False) -> int:
    """Solo parsea y muestra informacion del problema sin resolver."""
    if not path.exists():
        print(f"Error: Archivo no encontrado: {path}")
        return 1

    try:
        with open(path, 'r') as f:
            content = f.read()

        from src.parser import LPParser, MultiLPParser
        from src.matrix import LPBuilder

        if '---' in content:
            parser = MultiLPParser(content)
            problems = parser.parse_all()
            print(f"\n  Problemas encontrados: {len(problems)}")
            for i, p in enumerate(problems, 1):
                print(f"\n  --- Problema {i} ---")
                print(f"  Variables: {len(p.variables)}")
                print(f"  Restricciones: {len(p.constraints)}")
                print(f"  Tipo: {p.sense}")
                lp = LPBuilder(p).build()
                n_rows = lp.constraints.shape[0] if hasattr(lp, 'constraints') else '?'
                n_cols = lp.objective.shape[0] if hasattr(lp, 'objective') else '?'
                print(f"  Matriz: {n_rows}x{n_cols} (Polars LP)")
            print()
        else:
            parser_obj = LPParser(content)
            problem = parser_obj.parse()
            lp = LPBuilder(problem).build()
            print(f"\n  Problema: {path.name}")
            print(f"  Variables: {len(problem.variables)}")
            print(f"  Restricciones: {len(problem.constraints)}")
            print(f"  Tipo: {problem.sense}")
            n_rows = lp.constraints.shape[0] if hasattr(lp, 'constraints') else '?'
            n_cols = lp.objective.shape[0] if hasattr(lp, 'objective') else '?'
            print(f"  Matriz: {n_rows}x{n_cols} (Polars LP)")
            print(f"  Variables: {', '.join(problem.variables)}")
            print()
        return 0
    except Exception as e:
        print(f"Error al parsear: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
