"""
Exportacion de resultados de benchmarking.
Genera reportes y tablas (la visualizacion esta en src.visualization).
"""

from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

import numpy as np

from src.solver.benchmark import BenchmarkRunner
# Import BenchmarkPlotter in function to avoid circular import
# from src.visualization import BenchmarkPlotter


def performance_profile(
    results: List,
    time_col: str = "total_time",
    solver_col: str = "solver_name",
    tau_max: float = 10.0,
    num_points: int = 100,
) -> Dict[str, tuple]:
    """Calcula perfiles de Dolan-More a partir de resultados de benchmark.

    Para cada problema, calcula la razon del tiempo de cada solver contra
    el mejor tiempo. Luego genera la funcion de distribucion acumulada
    rho(tau) = proporcion de problemas resueltos con razon <= tau.

    Args:
        results: Lista de objetos con atributos problem_name, solver_name, total_time.
        time_col: Nombre del atributo de tiempo (default: total_time).
        solver_col: Nombre del atributo del solver (default: solver_name).
        tau_max: Maximo valor de tau a considerar.
        num_points: Numero de puntos para la curva.

    Returns:
        Dict con {solver_name: (tau_values, rho_values)}.
    """
    problemas = {}
    for r in results:
        prob = getattr(r, "problem_name", "")
        solver = getattr(r, solver_col, "")
        tiempo = getattr(r, time_col, 0.0)
        if prob not in problemas:
            problemas[prob] = {}
        if solver not in problemas[prob] or tiempo < problemas[prob][solver]:
            problemas[prob][solver] = tiempo

    solvers_set = set()
    for prob_data in problemas.values():
        solvers_set.update(prob_data.keys())
    solvers_list = sorted(solvers_set)

    perfiles = {}
    for solver in solvers_list:
        ratios = []
        for prob_data in problemas.values():
            if solver in prob_data:
                best_time = min(prob_data.values())
                if best_time > 0:
                    ratios.append(prob_data[solver] / best_time)
        if not ratios:
            continue
        ratios.sort()
        tau_values = np.linspace(1.0, tau_max, num_points)
        rho_values = [
            sum(1 for r in ratios if r <= tau) / len(ratios)
            for tau in tau_values
        ]
        perfiles[solver] = (tau_values, rho_values)

    return perfiles


class ResultsExporter:
    """Exportador de resultados de benchmarking a multiple formatos."""
    
    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner
        self.results = runner.results
        self.summary = runner.get_summary()
    
    def to_markdown(self, path: Path) -> None:
        """Exporta resultados a formato Markdown."""
        lines = [
            "# Reporte de Benchmarking",
            f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n## Resumen",
            f"- Total de pruebas: {self.summary['total_benchmarks']}",
            f"- Exitosas: {self.summary['successful']}",
            f"- Fallidas: {self.summary['failed']}",
            "\n## Por Solver",
        ]
        
        lines.append("\n| Solver | Pruebas | Exitosas | Tiempo Promedio |")
        lines.append("|--------|---------|----------|-----------------|")
        
        for solver, data in self.summary["by_solver"].items():
            avg_time = data["avg_time"] * 1000
            lines.append(f"| {solver} | {data['runs']} | {data['successful']} | {avg_time:.2f}ms |")
        
        lines.append("\n## Detalle de Resultados")
        
        lines.append("\n| Problema | Solver | Estado | Valor Obj. | Tiempo |")
        lines.append("|----------|--------|--------|------------|--------|")
        
        for r in self.results:
            status_icon = "OK" if r.solution.is_optimal() else "X"
            obj_val = f"{r.solution.objective_value:.2f}" if r.solution.objective_value else "-"
            lines.append(f"| {r.problem_name} | {r.solver_name} | {status_icon} | {obj_val} | {r.total_time*1000:.2f}ms |")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write("\n".join(lines))
    
    def to_html(self, path: Path, include_plots: bool = True, plots_dir: Optional[Path] = None) -> None:
        """Exporta resultados a formato HTML."""
        plots_html = ""
        if include_plots and plots_dir:
            # Import here to avoid circular import
            from src.visualization.benchmark_plots import BenchmarkPlotter
            plots_dir.mkdir(parents=True, exist_ok=True)
            plotter = BenchmarkPlotter(self.runner)
            paths = {
                'times': plots_dir / "benchmark_times.png",
                'success': plots_dir / "benchmark_success.png",
                'profile': plots_dir / "benchmark_profile.png",
                'dashboard': plots_dir / "benchmark_dashboard.png",
            }
            plotter.plot_times_comparison(paths['times'])
            plotter.plot_success_rate(paths['success'])
            plotter.plot_performance_profile(paths['profile'])
            plotter.plot_summary_dashboard(paths['dashboard'])
            
            plots_html = "\n## Graficos\n"
            for name, plot_path in paths.items():
                plots_html += f'\n![{name}]({plot_path.name})\n'
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #003366; }}
        h2 {{ color: #0066CC; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #003366; color: white; }}
        tr:nth-child(even) {{ background-color: #f8f8f8; }}
        .success {{ color: #228B22; font-weight: bold; }}
        .error {{ color: #DC143C; font-weight: bold; }}
        .summary {{ background-color: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        img {{ max-width: 100%; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Reporte de Benchmarking</h1>
    <p>Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>Resumen</h2>
        <ul>
            <li><strong>Total de pruebas:</strong> {self.summary['total_benchmarks']}</li>
            <li><strong>Exitosas:</strong> {self.summary['successful']}</li>
            <li><strong>Fallidas:</strong> {self.summary['failed']}</li>
        </ul>
    </div>
    
    <h2>Por Solver</h2>
    <table>
        <tr>
            <th>Solver</th>
            <th>Pruebas</th>
            <th>Exitosas</th>
            <th>Tiempo Promedio</th>
        </tr>
        {''.join(f"<tr><td>{solver}</td><td>{data['runs']}</td><td>{data['successful']}</td><td>{data['avg_time']*1000:.2f}ms</td></tr>" for solver, data in self.summary["by_solver"].items())}
    </table>
    
    <h2>Detalle de Resultados</h2>
    <table>
        <tr>
            <th>Problema</th>
            <th>Solver</th>
            <th>Estado</th>
            <th>Valor Obj.</th>
            <th>Tiempo</th>
        </tr>
        {''.join(f"<tr><td>{r.problem_name}</td><td>{r.solver_name}</td><td class=\"{'success' if r.solution.is_optimal() else 'error'}\">{r.solution.status}</td><td>{r.solution.objective_value if r.solution.objective_value else '-'}</td><td>{r.total_time*1000:.2f}ms</td></tr>" for r in self.results)}
    </table>
    
    {plots_html}
</body>
</html>
"""
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(html)
    
    def to_polars_dataframe(self):
        """Convierte resultados a un Polars DataFrame."""
        import polars as pl
        
        data = []
        for r in self.results:
            data.append({
                "problem": r.problem_name,
                "solver": r.solver_name,
                "status": r.solution.status,
                "objective_value": r.solution.objective_value,
                "parse_time_ms": r.parse_time * 1000,
                "build_time_ms": r.build_time * 1000,
                "solve_time_ms": r.stats.solve_time * 1000,
                "total_time_ms": r.total_time * 1000,
                "iterations": r.stats.iterations,
                "nodes": r.stats.nodes,
                "error": r.error
            })
        
        return pl.DataFrame(data)


def export_benchmark_results(
    runner: BenchmarkRunner,
    output_dir: Path,
    formats: List[str] = ["json", "csv", "md", "html"],
    include_plots: bool = True
) -> Dict[str, Path]:
    """
    Exporta todos los resultados de benchmarking.
    
    Args:
        runner: BenchmarkRunner con los resultados
        output_dir: Directorio de salida
        formats: Formatos a exportar (json, csv, md, html)
        include_plots: Si generar graficos (usando src.visualization)
        
    Returns:
        Diccionario con las rutas de archivos generados
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    
    exporter = ResultsExporter(runner)
    
    if "json" in formats:
        paths["json"] = output_dir / "benchmark_results.json"
        runner.export_json(paths["json"])
    
    if "csv" in formats:
        paths["csv"] = output_dir / "benchmark_results.csv"
        runner.export_csv(paths["csv"])
    
    if "md" in formats:
        paths["md"] = output_dir / "benchmark_report.md"
        exporter.to_markdown(paths["md"])
    
    if "html" in formats:
        plots_dir = output_dir / "plots" if include_plots else None
        paths["html"] = output_dir / "benchmark_report.html"
        exporter.to_html(paths["html"], include_plots=include_plots, plots_dir=plots_dir)
    
    return paths
