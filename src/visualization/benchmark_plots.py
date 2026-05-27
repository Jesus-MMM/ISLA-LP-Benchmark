"""
Funciones de visualización para resultados de benchmarking.
Genera gráficos comparativos y reportes visuales.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from src.analysis.benchmark_results import performance_profile
from src.solver.benchmark import BenchmarkRunner


@dataclass
class PlotStyle:
    """Estilos para los gráficos."""
    primary_color: str = "#003366"
    secondary_color: str = "#0066CC"
    success_color: str = "#228B22"
    error_color: str = "#DC143C"
    warning_color: str = "#FF8C00"
    grid_alpha: float = 0.3
    figure_size: tuple = (10, 6)
    font_size: int = 10


class BenchmarkPlotter:
    """
    Genera visualizaciones para resultados de benchmarking.
    Responsabilidad: solo gráficos y plots.
    """
    
    def __init__(self, runner: BenchmarkRunner, style: Optional[PlotStyle] = None):
        self.runner = runner
        self.style = style or PlotStyle()
        self.results = runner.results
        self.summary = runner.get_summary()
    
    def plot_times_comparison(self, save_path: Optional[Path] = None) -> None:
        """Gráfica comparación de tiempos por solver y problema."""
        if not self.results:
            return
        
        solvers = list(self.summary["by_solver"].keys())
        problems = list(self.summary["by_problem"].keys())
        
        fig, ax = plt.subplots(figsize=self.style.figure_size)
        
        x = np.arange(len(problems))
        width = 0.8 / max(len(solvers), 1)
        
        colors = plt.cm.Set2(np.linspace(0, 1, len(solvers)))
        
        for i, solver in enumerate(solvers):
            times = []
            for problem in problems:
                found = False
                for r in self.results:
                    if r.solver_name == solver and r.problem_name == problem:
                        times.append(r.total_time * 1000)
                        found = True
                        break
                if not found:
                    times.append(0)
            
            offset = (i - len(solvers)/2 + 0.5) * width
            ax.bar(x + offset, times, width, label=solver, color=colors[i])
        
        ax.set_xlabel('Problemas', fontsize=self.style.font_size)
        ax.set_ylabel('Tiempo (ms)', fontsize=self.style.font_size)
        ax.set_title('Comparación de Tiempos de Resolución', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(problems, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=self.style.grid_alpha, linestyle='--')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    def plot_success_rate(self, save_path: Optional[Path] = None) -> None:
        """Gráfica tasa de éxito por solver."""
        if not self.results:
            return
        
        fig, ax = plt.subplots(figsize=self.style.figure_size)
        
        solvers = list(self.summary["by_solver"].keys())
        total = []
        successful = []
        
        for solver in solvers:
            total.append(self.summary["by_solver"][solver]["runs"])
            successful.append(self.summary["by_solver"][solver]["successful"])
        
        x = np.arange(len(solvers))
        width = 0.35
        
        ax.bar(x - width/2, total, width, label='Total', color=self.style.secondary_color)
        bars2 = ax.bar(x + width/2, successful, width, label='Exitosos', color=self.style.success_color)
        
        ax.set_xlabel('Solver', fontsize=self.style.font_size)
        ax.set_ylabel('Número de Pruebas', fontsize=self.style.font_size)
        ax.set_title('Tasa de Éxito por Solver', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(solvers)
        ax.legend()
        ax.grid(True, alpha=self.style.grid_alpha, linestyle='--', axis='y')
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{int(height)}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    def plot_performance_profile(self, save_path: Optional[Path] = None) -> None:
        """Gráfica perfil de rendimiento estilo Dolan-Moré."""
        if not self.results:
            return
        
        perfiles = performance_profile(
            self.results,
            time_col="total_time",
            solver_col="solver_name",
            tau_max=10.0,
            num_points=100,
        )
        
        fig, ax = plt.subplots(figsize=self.style.figure_size)
        
        colors = plt.cm.Set2(np.linspace(0, 1, len(perfiles)))
        
        for i, (solver, (tau, rho)) in enumerate(sorted(perfiles.items())):
            ax.step(tau, rho, label=solver, where='post', color=colors[i], linewidth=2)
        
        ax.set_xlabel(r'Ratio de Tiempo ($\tau$)', fontsize=self.style.font_size)
        ax.set_ylabel(r'$\rho(\tau)$ — Fracción de Problemas', fontsize=self.style.font_size)
        ax.set_title('Perfil de Rendimiento (Dolan-Moré)', fontsize=14, fontweight='bold')
        ax.set_xlim(1.0, 10.0)
        ax.set_ylim(0, 1.05)
        ax.legend(loc='lower right')
        ax.grid(True, alpha=self.style.grid_alpha, linestyle='--')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    def plot_summary_dashboard(self, save_path: Optional[Path] = None) -> None:
        """Genera un dashboard con todas las métricas."""
        if not self.results:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        title = f"Dashboard de Benchmarking\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        ax1 = axes[0, 0]
        solvers = list(self.summary["by_solver"].keys())
        avg_times = [self.summary["by_solver"][s]["avg_time"] * 1000 for s in solvers]
        bars = ax1.barh(solvers, avg_times, color=self.style.primary_color)
        ax1.set_xlabel('Tiempo Promedio (ms)')
        ax1.set_title('Tiempo Promedio por Solver')
        ax1.grid(True, alpha=self.style.grid_alpha, axis='x')
        for bar, time in zip(bars, avg_times):
            ax1.text(time + 0.1, bar.get_y() + bar.get_height()/2, f'{time:.2f}ms', 
                    va='center', fontsize=9)
        
        ax2 = axes[0, 1]
        total = [self.summary["by_solver"][s]["runs"] for s in solvers]
        successful = [self.summary["by_solver"][s]["successful"] for s in solvers]
        x = np.arange(len(solvers))
        ax2.bar(x - 0.2, total, 0.4, label='Total', color=self.style.secondary_color)
        ax2.bar(x + 0.2, successful, 0.4, label='Exitosos', color=self.style.success_color)
        ax2.set_xticks(x)
        ax2.set_xticklabels(solvers)
        ax2.set_title('Tasa de Éxito')
        ax2.legend()
        ax2.grid(True, alpha=self.style.grid_alpha, axis='y')
        
        ax3 = axes[1, 0]
        problems = list(self.summary["by_problem"].keys())
        problem_times = {}
        for problem in problems:
            problem_times[problem] = []
            for r in self.results:
                if r.problem_name == problem and r.solution.is_optimal():
                    problem_times[problem].append(r.total_time * 1000)
        
        ax3.boxplot([problem_times[p] for p in problems], labels=problems)
        ax3.set_ylabel('Tiempo (ms)')
        ax3.set_title('Distribución de Tiempos por Problema')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=self.style.grid_alpha, axis='y')
        
        ax4 = axes[1, 1]
        categories = ['Total', 'Exitosos', 'Fallidos']
        values = [
            self.summary['total_benchmarks'],
            self.summary['successful'],
            self.summary['failed']
        ]
        colors = [self.style.secondary_color, self.style.success_color, self.style.error_color]
        wedges, texts, autotexts = ax4.pie(values, labels=categories, colors=colors, 
                                           autopct='%1.1f%%', startangle=90)
        ax4.set_title('Resumen General')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
        else:
            plt.show()

    def generate_all_plots(self, output_dir: Path) -> None:
        """Genera todos los gráficos de benchmarking en el directorio especificado."""
        output_dir.mkdir(parents=True, exist_ok=True)
        self.plot_times_comparison(output_dir / "benchmark_times.png")
        self.plot_success_rate(output_dir / "benchmark_success.png")
        self.plot_performance_profile(output_dir / "benchmark_profile.png")
        self.plot_summary_dashboard(output_dir / "benchmark_dashboard.png")

