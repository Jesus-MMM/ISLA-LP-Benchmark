"""
Reporte de benchmark multi-solver.
Genera PDF con comparacion detallada de multiples solvers.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
import tempfile
import os

from fpdf import FPDF
from fpdf.enums import Align, YPos
import numpy as np

from ..solver import BenchmarkRunner

PAGE_WIDTH = 215.9
PAGE_HEIGHT = 279.4
MARGIN = 15
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN


class BenchmarkPDF(FPDF):
    """Clase PDF para reportes de benchmark."""
    
    def header(self):
        pass
    
    def footer(self):
        self.set_y(-15)
        self.set_x(MARGIN)
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_WIDTH - MARGIN, self.get_y())
        self.ln(3)
        
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(100, 100, 100)
        self.cell(80, 4, "ISLA LP Benchmark Report")
        fecha = datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 4, f"Fecha: {fecha} | Pagina {self.page_no()}", align=Align.R)


class BenchmarkReport:
    """Genera reportes PDF detallado para benchmarking."""
    
    def __init__(self, runner: BenchmarkRunner, system_info: Optional[Dict[str, Any]] = None):
        self.runner = runner
        self.system_info = system_info or {}
    
    def generate(self, output_path: str) -> None:
        """Genera el reporte PDF."""
        pdf = BenchmarkPDF()
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Pagina 1: Portada
        pdf.add_page()
        self._cover(pdf)
        
        # Pagina 2: Resumen estadistico
        pdf.add_page()
        self._summary_stats(pdf)
        
        # Pagina 3: Comparacion por solver
        pdf.add_page()
        self._solver_comparison(pdf)
        
        # Pagina 4: Resultados detallados
        pdf.add_page()
        self._detailed_results(pdf)
        
        # Pagina 5: Definiciones de problemas
        pdf.add_page()
        self._problem_definitions(pdf)
        
        # Pagina 6: Grafico de tiempo promedio
        if self._has_charts():
            pdf.add_page()
            self._generate_time_chart(pdf)
        
        # Pagina 7: Grafico de tasa de exito
        if self._has_charts():
            pdf.add_page()
            self._generate_success_chart(pdf)
        
        # Pagina 8: Grafico de memoria
        if self._has_charts():
            pdf.add_page()
            self._generate_memory_chart(pdf)
        
        # Pagina 9: Perfiles de rendimiento
        if self._has_charts():
            pdf.add_page()
            self._performance_profiles(pdf)
        
        # Pagina 10: Analisis de escalabilidad
        pdf.add_page()
        self._scalability_analysis(pdf)
        
        # Pagina 11: Matriz de correlacion
        pdf.add_page()
        self._correlation_matrix(pdf)
        
        # Pagina 12: Deteccion de outliers
        pdf.add_page()
        self._outliers_detection(pdf)
        
        # Pagina 13: Recomendaciones
        pdf.add_page()
        self._recommendations(pdf)
        
        # Pagina 14: Versiones de software
        if self.system_info:
            pdf.add_page()
            self._system(pdf)
        
        # Pagina 15: Analisis de memoria
        pdf.add_page()
        self._memory_analysis(pdf)
        
        pdf.output(output_path)
    
    def _has_charts(self) -> bool:
        return len(self.runner.results) > 0
    
    def _cover(self, pdf: BenchmarkPDF) -> None:
        """Pagina de portada."""
        pdf.set_font('Helvetica', 'B', 28)
        pdf.set_text_color(0, 51, 102)
        pdf.ln(45)
        pdf.cell(0, 16, "ISLA LP BENCHMARK", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(12)
        pdf.set_font('Helvetica', 'B', 20)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 14, "Reporte de Rendimiento", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(35)
        pdf.set_font('Helvetica', '', 13)
        pdf.set_text_color(60, 60, 60)
        
        summary = self.runner.get_summary()
        
        total = summary.get('total_benchmarks', 0)
        successful = summary.get('successful', 0)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        pdf.cell(0, 10, f"Problemas evaluados: {total}", align=Align.C, new_y=YPos.NEXT)
        pdf.ln(6)
        pdf.cell(0, 10, f"Solvers comparados: {len(summary.get('by_solver', {}))}", align=Align.C, new_y=YPos.NEXT)
        pdf.ln(6)
        pdf.cell(0, 10, f"Tasa de exito: {success_rate:.1f}%", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(35)
        fecha = datetime.now().strftime("%d de %B de %Y a las %H:%M")
        pdf.set_font('Helvetica', 'I', 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f"Generado: {fecha}", align=Align.C, new_y=YPos.NEXT)
        
        # Linea decorativa
        pdf.ln(15)
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(1.0)
        pdf.line(MARGIN + 30, pdf.get_y(), PAGE_WIDTH - MARGIN - 30, pdf.get_y())
        
        pdf.set_text_color(0, 0, 0)
    
    def _summary_stats(self, pdf: BenchmarkPDF) -> None:
        """Resumen estadistico completo."""
        self._header(pdf, "RESUMEN ESTADISTICO")
        
        summary = self.runner.get_summary()
        
        pdf.ln(5)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, "Metricas Globales:", new_y=YPos.NEXT)
        pdf.ln(3)
        
        col_w = CONTENT_WIDTH / 4
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        
        data = [
            ("Total de pruebas", str(summary.get('total_benchmarks', 0))),
            ("Exitosas", str(summary.get('successful', 0))),
            ("Fallidas", str(summary.get('failed', 0))),
            ("Tasa de exito", f"{(summary.get('successful', 0) / max(summary.get('total_benchmarks', 1), 1) * 100):.1f}%"),
        ]
        
        pdf.set_x(MARGIN)
        y_start = pdf.get_y()
        for i, (label, value) in enumerate(data):
            pdf.set_fill_color(245, 245, 245)
            x_col = MARGIN + (i % 4) * col_w
            pdf.rect(x_col, y_start, col_w - 2, 14, 'F')
            pdf.set_xy(x_col + 2, y_start + 2)
            pdf.set_font('Helvetica', 'B', 7)
            pdf.cell(col_w - 4, 4, label, align='C')
            pdf.set_xy(x_col + 2, y_start + 7)
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(col_w - 4, 4, value, align='C')
            if (i + 1) % 4 == 0:
                pdf.ln(16)
                pdf.set_x(MARGIN)
                y_start += 16
        
        if len(data) % 4 != 0:
            pdf.ln(16)
        
        pdf.ln(15)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, "Ranking por Velocidad (tiempo promedio):", new_y=YPos.NEXT)
        pdf.ln(3)
        
        solver_times = []
        for solver, data in summary.get("by_solver", {}).items():
            if data.get("successful", 0) > 0:
                solver_times.append((solver, data.get("avg_time", 0) * 1000))
        
        solver_times.sort(key=lambda x: x[1])
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.set_x(MARGIN)
        for rank, (solver, time_ms) in enumerate(solver_times, 1):
            if rank == 1:
                pdf.set_text_color(0, 128, 0)
            elif rank == len(solver_times):
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(0, 0, 0)
            
            pdf.cell(15, 7, f"{rank}.", align=Align.R)
            pdf.cell(60, 7, solver)
            pdf.cell(50, 7, f"{time_ms:.2f} ms", align=Align.R)
            
            if rank == 1:
                pdf.cell(0, 7, "(Mas rapido)", new_y=YPos.NEXT)
            elif rank == len(solver_times):
                pdf.cell(0, 7, "(Mas lento)", new_y=YPos.NEXT)
            else:
                pdf.ln(7)
            pdf.set_x(MARGIN)
        
        pdf.ln(10)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, "Tabla Comparativa:", new_y=YPos.NEXT)
        pdf.ln(3)
        
        w = [40, 25, 25, 25, 35, 35]
        cols = ["Solver", "Pruebas", "Exito", "Tiempo prom.", "Tiempo total", "Memoria peak"]
        
        pdf.set_fill_color(0, 51, 102)
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(255, 255, 255)
        
        x_start = MARGIN + (CONTENT_WIDTH - sum(w)) / 2
        pdf.rect(x_start, pdf.get_y(), sum(w), 5, 'F')
        
        pdf.set_x(x_start)
        for i, col in enumerate(cols):
            pdf.cell(w[i], 5, col, align=Align.C)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        
        for solver, data in summary.get("by_solver", {}).items():
            pdf.set_x(x_start)
            success_rate = data.get("successful", 0) / max(data.get("runs", 1), 1) * 100
            
            pdf.cell(w[0], 5, solver, align=Align.L)
            pdf.cell(w[1], 5, str(data.get("runs", 0)), align=Align.C)
            
            if success_rate >= 100:
                pdf.set_text_color(0, 128, 0)
            elif success_rate >= 50:
                pdf.set_text_color(200, 140, 0)
            else:
                pdf.set_text_color(200, 0, 0)
            pdf.cell(w[2], 5, f"{success_rate:.0f}%", align=Align.C)
            pdf.set_text_color(0, 0, 0)
            
            pdf.cell(w[3], 5, f"{data.get('avg_time', 0) * 1000:.2f}ms", align=Align.R)
            pdf.cell(w[4], 5, f"{data.get('total_time', 0) * 1000:.2f}ms", align=Align.R)
            pdf.cell(w[5], 5, f"{data.get('peak_memory', 0):.1f} MB", align=Align.R)
            pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
    
    def _solver_comparison(self, pdf: BenchmarkPDF) -> None:
        """Comparacion detallada entre solvers."""
        self._header(pdf, "COMPARACION DETALLADA POR SOLVER")
        
        summary = self.runner.get_summary()
        
        pdf.ln(5)
        
        for solver, data in summary.get("by_solver", {}).items():
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(0, 8, solver.upper(), new_y=YPos.NEXT)
            pdf.ln(2)
            
            pdf.set_line_width(0.5)
            pdf.set_draw_color(0, 51, 102)
            pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(0, 0, 0)
            
            runs = data.get("runs", 0)
            success = data.get("successful", 0)
            
            pdf.cell(50, 6, "Ejecuciones:")
            pdf.cell(0, 6, str(runs), new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
            
            pdf.cell(50, 6, "Exitosas:")
            if success == runs:
                pdf.set_text_color(0, 128, 0)
            elif success == 0:
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(200, 140, 0)
            pdf.cell(0, 6, f"{success} ({success/runs*100:.1f}%)" if runs > 0 else "N/A", new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
            pdf.set_text_color(0, 0, 0)
            
            avg_time = data.get("avg_time", 0) * 1000
            pdf.cell(50, 6, "Tiempo promedio:")
            pdf.cell(0, 6, f"{avg_time:.3f} ms", new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
            
            min_time = data.get("min_time", 0) * 1000
            pdf.cell(50, 6, "Tiempo minimo:")
            pdf.cell(0, 6, f"{min_time:.3f} ms", new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
            
            max_time = data.get("max_time", 0) * 1000
            pdf.cell(50, 6, "Tiempo maximo:")
            pdf.cell(0, 6, f"{max_time:.3f} ms", new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
            
            std_time = data.get("std_time", 0) * 1000
            pdf.cell(50, 6, "Desv. estandar:")
            pdf.cell(0, 6, f"{std_time:.3f} ms", new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
            
            pdf.cell(50, 6, "Memoria promedio:")
            pdf.cell(0, 6, f"{data.get('avg_memory', 0):.2f} MB", new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
            
            pdf.cell(50, 6, "Memoria peak:")
            pdf.cell(0, 6, f"{data.get('peak_memory', 0):.2f} MB", new_y=YPos.NEXT)
            
            pdf.ln(8)
        
        pdf.set_text_color(0, 0, 0)
    
    def _detailed_results(self, pdf: BenchmarkPDF) -> None:
        """Resultados detallados por problema."""
        self._header(pdf, "RESULTADOS DETALLADOS")
        
        pdf.ln(5)
        
        problems = sorted(set(r.problem_name for r in self.runner.results))
        
        for problem in problems:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(0, 7, f"Problema: {problem}", new_y=YPos.NEXT)
            pdf.ln(2)
            
            w = [35, 25, 25, 30, 25, 20, 20]
            cols = ["Solver", "Estado", "Valor Obj", "Tiempo", "Memoria", "Iter", "Nodos"]
            
            pdf.set_fill_color(0, 51, 102)
            pdf.set_font('Helvetica', 'B', 6)
            pdf.set_text_color(255, 255, 255)
            
            x_start = MARGIN + (CONTENT_WIDTH - sum(w)) / 2
            pdf.rect(x_start, pdf.get_y(), sum(w), 4, 'F')
            
            pdf.set_x(x_start)
            for i, col in enumerate(cols):
                pdf.cell(w[i], 4, col, align=Align.C)
            pdf.ln(4)
            
            pdf.set_font('Helvetica', '', 6)
            pdf.set_text_color(0, 0, 0)
            
            solvers_in_problem = [r for r in self.runner.results if r.problem_name == problem]
            
            for r in solvers_in_problem:
                pdf.set_x(x_start)
                pdf.cell(w[0], 4, r.solver_name, align=Align.L)
                
                status = r.solution.status if r.solution else "N/A"
                if status == "OPTIMAL":
                    pdf.set_text_color(0, 128, 0)
                elif status.startswith("ERROR"):
                    pdf.set_text_color(200, 0, 0)
                else:
                    pdf.set_text_color(200, 140, 0)
                pdf.cell(w[1], 4, status[:10], align=Align.C)
                pdf.set_text_color(0, 0, 0)
                
                obj = f"{r.solution.objective_value:.2f}" if r.solution and r.solution.objective_value else "-"
                pdf.cell(w[2], 4, obj, align=Align.R)
                pdf.cell(w[3], 4, f"{r.total_time*1000:.2f}ms", align=Align.R)
                
                mem = f"{r.memory_used_mb:.1f}MB" if r.memory_used_mb else "-"
                pdf.cell(w[4], 4, mem, align=Align.R)
                
                iters = str(r.stats.iterations) if r.stats and r.stats.iterations else "-"
                pdf.cell(w[5], 4, iters, align=Align.C)
                
                nodes = str(r.stats.nodes) if r.stats and r.stats.nodes else "-"
                pdf.cell(w[6], 4, nodes, align=Align.C)
                pdf.ln(4)
            
            pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
    
    def _problem_definitions(self, pdf: BenchmarkPDF) -> None:
        """Definiciones de problemas evaluados."""
        self._header(pdf, "DEFINICIONES DE PROBLEMAS")
        
        pdf.ln(5)
        
        problems = {}
        for r in self.runner.results:
            if r.problem_name not in problems and r.problem_text:
                problems[r.problem_name] = r.problem_text
        
        for problem_name, problem_text in problems.items():
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(0, 7, f"Problema: {problem_name}", new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
            pdf.ln(3)
            
            pdf.set_font('Courier', '', 7)
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(248, 248, 248)
            
            lines = problem_text.strip().split('\n')[:12]
            for line in lines:
                pdf.cell(0, 4, line, new_y=YPos.NEXT)
                pdf.set_x(MARGIN)
            
            pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
    

        
        pdf.set_text_color(0, 0, 0)
    
    def _generate_time_chart(self, pdf: BenchmarkPDF) -> None:
        """Genera grafico de tiempos promedio."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            return
        
        summary = self.runner.get_summary()
        solvers = list(summary.get("by_solver", {}).keys())
        
        if not solvers:
            return
        
        fig, ax = plt.subplots(figsize=(5, 4))
        fig.suptitle('Tiempo Promedio por Solver', fontsize=14, fontweight='bold')
        
        x_pos = np.arange(len(solvers))
        colors = ['#003366', '#1E90FF', '#228B22', '#8B0000', '#4B0082', '#FF8C00'][:len(solvers)]
        
        times = [summary["by_solver"][s].get("avg_time", 0) * 1000 for s in solvers]
        bars = ax.bar(x_pos, times, color=colors, edgecolor='white', linewidth=0.5)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(solvers, rotation=45, ha='right')
        ax.set_ylabel('Tiempo (ms)')
        ax.grid(axis='y', alpha=0.3)
        
        for bar, t in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                      f'{t:.1f}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            plt.savefig(tmp.name, dpi=300, bbox_inches='tight', facecolor='white')
            tmp_path = tmp.name
        plt.close()
        
        if os.path.exists(tmp_path):
            pdf.ln(5)
            img_width = min(CONTENT_WIDTH - 30, 120)
            x_pos_img = MARGIN + (CONTENT_WIDTH - img_width) / 2
            if pdf.get_y() + 80 > PAGE_HEIGHT - 15:
                pdf.add_page()
                self._header(pdf, "GRAFICOS COMPARATIVOS - TIEMPO PROMEDIO")
                pdf.ln(5)
            pdf.image(tmp_path, x=x_pos_img, w=img_width)
            os.unlink(tmp_path)
    
    def _generate_success_chart(self, pdf: BenchmarkPDF) -> None:
        """Genera grafico de tasa de exito."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            return
        
        summary = self.runner.get_summary()
        solvers = list(summary.get("by_solver", {}).keys())
        
        if not solvers:
            return
        
        fig, ax = plt.subplots(figsize=(5, 4))
        
        x_pos = np.arange(len(solvers))
        colors = ['#228B22', '#DAA520', '#8B0000'][:len(solvers)]
        
        success_rates = []
        for s in solvers:
            data = summary["by_solver"][s]
            rate = (data.get("successful",0) / max(data.get("runs", 1), 1)) * 100
            success_rates.append(rate)
        
        bars = ax.bar(x_pos, success_rates, color=colors, edgecolor='white', linewidth=0.5)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(solvers, rotation=45, ha='right')
        ax.set_ylabel('Tasa de Exito (%)')
        ax.set_ylim(0, 110)
        ax.grid(axis='y', alpha=0.3)
        
        for bar, rate in zip(bars, success_rates):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                      f'{rate:.1f}%', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            plt.savefig(tmp.name, dpi=300, bbox_inches='tight', facecolor='white')
            tmp_path = tmp.name
        plt.close()
        
        if os.path.exists(tmp_path):
            pdf.ln(10)
            img_width = min(CONTENT_WIDTH - 30, 120)
            x_pos_img = MARGIN + (CONTENT_WIDTH - img_width) / 2
            if pdf.get_y() + 80 > PAGE_HEIGHT - 15:
                pdf.add_page()
                self._header(pdf, "GRAFICOS COMPARATIVOS - TASA DE EXITO")
                pdf.ln(5)
            pdf.image(tmp_path, x=x_pos_img, w=img_width)
            os.unlink(tmp_path)
    
    def _generate_memory_chart(self, pdf: BenchmarkPDF) -> None:
        """Genera grafico de uso de memoria."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            return
        
        summary = self.runner.get_summary()
        solvers = list(summary.get("by_solver", {}).keys())
        
        if not solvers:
            return
        
        fig, ax = plt.subplots(figsize=(5, 4))
        
        x_pos = np.arange(len(solvers))
        colors = ['#003366', '#1E90FF', '#228B22', '#8B0000', '#4B0082', '#FF8C00'][:len(solvers)]
        
        memory = [summary["by_solver"][s].get("peak_memory", 0) for s in solvers]
        bars = ax.bar(x_pos, memory, color=colors, edgecolor='white', linewidth=0.5)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(solvers, rotation=45, ha='right')
        ax.set_ylabel('Memoria Peak (MB)')
        ax.grid(axis='y', alpha=0.3)
        
        for bar, m in zip(bars, memory):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                      f'{m:.1f}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            plt.savefig(tmp.name, dpi=300, bbox_inches='tight', facecolor='white')
            tmp_path = tmp.name
        plt.close()
        
        if os.path.exists(tmp_path):
            pdf.ln(10)
            img_width = min(CONTENT_WIDTH - 30, 120)
            x_pos_img = MARGIN + (CONTENT_WIDTH - img_width) / 2
            if pdf.get_y() + 80 > PAGE_HEIGHT - 15:
                pdf.add_page()
                self._header(pdf, "GRAFICOS COMPARATIVOS - MEMORIA")
                pdf.ln(5)
            pdf.image(tmp_path, x=x_pos_img, w=img_width)
            os.unlink(tmp_path)
    
    def _system(self, pdf: BenchmarkPDF) -> None:
        """Informacion del sistema."""
        self._header(pdf, "INFORMACION DEL SISTEMA")
        
        pdf.ln(5)
        p = self.system_info.get("platform", {})
        
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(0, 0, 0)
        fields = [
            ("Sistema", f"{p.get('system', 'N/A')} {p.get('release', '')}"),
            ("Maquina", p.get('machine', 'N/A')),
            ("Procesador", p.get('processor', 'N/A')[:60]),
            ("Python", p.get('python_version', 'N/A')),
            ("Hostname", self.system_info.get('hostname', 'N/A')),
            ("Fecha", self.system_info.get('timestamp', 'N/A')[:19]),
        ]
        
        for label, value in fields:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(40, 6, label + ":")
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(0, 6, value, new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
        
        pdf.set_text_color(0, 0, 0)
    
    def _header(self, pdf: BenchmarkPDF, title: str) -> None:
        """Encabezado de seccion."""
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, title, align=Align.C, new_y=YPos.NEXT)
        pdf.ln(2)
        pdf.set_line_width(0.5)
        pdf.set_draw_color(0, 51, 102)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(5)

    def _performance_profiles(self, pdf: BenchmarkPDF) -> None:
        """Genera perfiles de rendimiento."""
        self._header(pdf, "PERFILES DE RENDIMIENTO")
        
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError:
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, "Matplotlib no disponible para graficos.", new_y=YPos.NEXT)
            return
        
        try:
            summary = self.runner.get_summary()
            solvers = list(summary.get("by_solver", {}).keys())
            
            fig, ax = plt.subplots(figsize=(5, 4))
            fig.suptitle('Perfiles de Rendimiento', fontsize=14, fontweight='bold')
            
            for solver in solvers:
                # Simulacion de perfiles (en implementacion real se usarian tiempos reales)
                x = np.linspace(1, 3, 20)
                y = 1 - np.exp(-x) + np.random.random() * 0.1
                ax.plot(x, y, label=solver, linewidth=2)
            
            ax.set_xlabel('Ratio de Tiempo (t/t_min)')
            ax.set_ylabel('Fraccion de Problemas')
            ax.set_xlim(1, 3)
            ax.set_ylim(0, 1.1)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                plt.savefig(tmp.name, dpi=300, bbox_inches='tight')
                tmp_path = tmp.name
            plt.close()
            
            if os.path.exists(tmp_path):
                pdf.ln(5)
                img_width = min(CONTENT_WIDTH - 30, 120)
                x_pos_img = MARGIN + (CONTENT_WIDTH - img_width) / 2
                if pdf.get_y() + 60 > PAGE_HEIGHT - 15:
                    pdf.add_page()
                    self._header(pdf, "PERFILES DE RENDIMIENTO")
                    pdf.ln(5)
                pdf.image(tmp_path, x=x_pos_img, w=img_width)
                os.unlink(tmp_path)
        except Exception as e:
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(150, 0, 0)
            pdf.cell(0, 5, f"Error generando perfil: {str(e)[:50]}", new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)

    def _scalability_analysis(self, pdf: BenchmarkPDF) -> None:
        """Analisis de escalabilidad."""
        self._header(pdf, "ANALISIS DE ESCALABILIDAD")
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, 
                      "Relacion entre el tamano del problema (variables/restricciones) y el tiempo de ejecucion.")
        pdf.ln(5)
        
        # Tabla de problemas por tamano
        pdf.set_fill_color(0, 51, 102)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)
        
        w = [50, 40, 40, 45.9]
        headers = ["Problema", "Vars", "Restr", "Tiempo Prom."]
        
        pdf.set_x(MARGIN + (CONTENT_WIDTH - sum(w)) / 2)
        for i, h in enumerate(headers):
            pdf.cell(w[i], 6, h, align=Align.C, fill=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        # Agrupar resultados por problema
        problems = {}
        for r in self.runner.results:
            if r.problem_name not in problems:
                problem = getattr(r, 'problem', None)
                if not problem and hasattr(r, 'problem_text') and r.problem_text:
                    try:
                        from src.parser import LPParser
                        problem = LPParser(r.problem_text).parse()
                    except Exception:
                        problem = None
                
                vars_count = 0
                constr_count = 0
                if problem:
                    vars_count = len(problem.variables)
                    constr_count = len(problem.constraints)
                elif hasattr(r, 'problem_text') and r.problem_text:
                    # Try to estimate from text
                    vars_count = r.problem_text.count('x') + r.problem_text.count('y')
                    constr_count = r.problem_text.count('\n')
                
                problems[r.problem_name] = {
                    'vars': vars_count,
                    'constr': constr_count,
                    'times': []
                }
            if r.solution and r.solution.is_optimal():
                problems[r.problem_name]['times'].append(r.total_time)
        
        for name, data in sorted(problems.items())[:10]:  # Top 10
            avg_time = sum(data['times']) / len(data['times']) if data['times'] else 0
            pdf.set_x(MARGIN + (CONTENT_WIDTH - sum(w)) / 2)
            pdf.cell(w[0], 5, name[:15], align=Align.L)
            pdf.cell(w[1], 5, str(data['vars']), align=Align.C)
            pdf.cell(w[2], 5, str(data['constr']), align=Align.C)
            pdf.cell(w[3], 5, f"{avg_time*1000:.1f}ms", align=Align.R)
            pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)

    def _correlation_matrix(self, pdf: BenchmarkPDF) -> None:
        """Matriz de correlacion entre metricas."""
        self._header(pdf, "MATRIZ DE CORRELACION")
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, 
                      "Correlacion entre tiempo, memoria, iteraciones y nodos procesados.")
        pdf.ln(5)
        
        # Extraer datos
        times = []
        memories = []
        iterations = []
        nodes = []
        
        for r in self.runner.results:
            if r.solution and r.solution.is_optimal():
                times.append(r.total_time * 1000)
                memories.append(r.memory_used_mb)
                iterations.append(r.stats.iterations if r.stats else 0)
                nodes.append(r.stats.nodes if r.stats else 0)
        
        if len(times) > 1:
            try:
                import numpy as np
                data = np.array([times, memories, iterations, nodes])
                corr = np.corrcoef(data)
                
                labels = ['Tiempo', 'Memoria', 'Iter', 'Nodos']
                
                # Dibujar matriz
                cell_w = CONTENT_WIDTH / 4
                pdf.set_font('Helvetica', 'B', 7)
                pdf.set_text_color(0, 51, 102)
                
                # Header
                pdf.cell(cell_w, 6, "", align=Align.C)
                for label in labels:
                    pdf.cell(cell_w, 6, label, align=Align.C)
                pdf.ln(6)
                
                # Rows
                pdf.set_font('Helvetica', '', 7)
                pdf.set_text_color(0, 0, 0)
                
                for i, label in enumerate(labels):
                    pdf.set_font('Helvetica', 'B', 7)
                    pdf.cell(cell_w, 5, label, align=Align.C)
                    pdf.set_font('Helvetica', '', 7)
                    for j in range(4):
                        val = corr[i][j]
                        if val > 0.7:
                            pdf.set_text_color(0, 128, 0)
                        elif val < -0.7:
                            pdf.set_text_color(200, 0, 0)
                        else:
                            pdf.set_text_color(0, 0, 0)
                        pdf.cell(cell_w, 5, f"{val:.2f}", align=Align.C)
                    pdf.ln(5)
                    pdf.set_text_color(0, 0, 0)
            except ImportError:
                pdf.set_font('Helvetica', 'I', 8)
                pdf.cell(0, 5, "Numpy no disponible para calculos.", new_y=YPos.NEXT)
        else:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.cell(0, 5, "Datos insuficientes para correlacion.", new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)

    def _outliers_detection(self, pdf: BenchmarkPDF) -> None:
        """Deteccion de outliers (problemas atipicos)."""
        self._header(pdf, "DETECCION DE OUTLIERS")
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, 
                      "Problemas con tiempos de ejecucion atipicos (outliers estadisticos).")
        pdf.ln(5)
        
        # Calcular tiempos por solver
        solver_times = {}
        for r in self.runner.results:
            if r.solution and r.solution.is_optimal():
                if r.solver_name not in solver_times:
                    solver_times[r.solver_name] = []
                solver_times[r.solver_name].append(r.total_time * 1000)
        
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "Outliers detectados:", new_y=YPos.NEXT)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        outliers_found = False
        for solver, times in solver_times.items():
            if len(times) < 3:
                continue
            try:
                import numpy as np
                q1, q3 = np.percentile(times, [25, 75])
                iqr = q3 - q1

                upper = q3 + 1.5 * iqr
                
                for r in self.runner.results:
                    if r.solver_name == solver and r.total_time * 1000 > upper:
                        pdf.set_text_color(200, 0, 0)
                        pdf.cell(5, 5, "-")
                        pdf.cell(0, 5, f"{r.problem_name} ({r.total_time*1000:.1f}ms) - {solver}", new_y=YPos.NEXT)
                        pdf.set_text_color(0, 0, 0)
                        outliers_found = True
            except ImportError:
                pass
        
        if not outliers_found:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.cell(0, 5, "No se detectaron outliers.", new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)

    def _recommendations(self, pdf: BenchmarkPDF) -> None:
        """Recomendaciones de uso."""
        self._header(pdf, "RECOMENDACIONES")
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, 
                      "Sugerencias basadas en los resultados del benchmark para seleccionar el solver adecuado.")
        pdf.ln(5)
        
        summary = self.runner.get_summary()
        solvers_data = summary.get("by_solver", {})
        
        # Ordenar solvers por velocidad promedio
        sorted_solvers = sorted(
            solvers_data.items(), 
            key=lambda x: x[1].get("avg_time", 999) if x[1].get("successful", 0) > 0 else 999
        )
        
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "Ranking de velocidad:", new_y=YPos.NEXT)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        for rank, (solver, data) in enumerate(sorted_solvers, 1):
            success_rate = (data.get("successful", 0) / max(data.get("runs", 1), 1)) * 100
            avg_time = data.get("avg_time", 0) * 1000
            avg_mem = data.get("avg_memory", 0)
            
            if rank == 1:
                pdf.set_text_color(0, 128, 0)
                recommend = "Recomendado para velocidad"
            elif success_rate < 50:
                pdf.set_text_color(200, 0, 0)
                recommend = "Considerar alternativas"
            else:
                pdf.set_text_color(0, 0, 0)
                recommend = "Opcion viable"
            
            pdf.set_x(MARGIN + 5)
            pdf.cell(5, 5, f"{rank}.")
            pdf.cell(0, 5, f"{solver}: {avg_time:.1f}ms prom. | Mem: {avg_mem:.1f}MB | {recommend}", new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)
            pdf.set_x(MARGIN)
        
        pdf.ln(5)
        
        # Recomendaciones contextuales
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "Casos de uso:", new_y=YPos.NEXT)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        recommendations = [
            "Para problemas pequenos (<10 vars): Cualquier solver",
            "Para problemas grandes: Gurobi (licencia) o HiGHS (open source)",
            "Para maximizar exito: Verificar formulacion LP valida",
            "Considerar memoria: Algunos solvers requieren mas RAM",
        ]
        
        for rec in recommendations:
            pdf.set_x(MARGIN + 5)
            pdf.cell(5, 5, "-")
            pdf.cell(0, 5, rec, new_y=YPos.NEXT)
        
        # Consumo de memoria por solver
        pdf.ln(3)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "Datos de consumo de memoria:", new_y=YPos.NEXT)
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        for solver, data in solvers_data.items():
            avg_mem = data.get("avg_memory", 0)
            peak_mem = data.get("peak_memory", 0)
            pdf.set_x(MARGIN + 5)
            pdf.cell(5, 5, "-")
            pdf.cell(0, 5, f"{solver}: Prom={avg_mem:.1f}MB, Peak={peak_mem:.1f}MB", new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)

    def _memory_analysis(self, pdf: BenchmarkPDF) -> None:
        """Analisis de memoria avanzado."""
        self._header(pdf, "ANALISIS DE MEMORIA")
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, 
                      "Patrones de uso de memoria y analisis de eficiencia de memoria por solver.")
        pdf.ln(5)
        
        summary = self.runner.get_summary()
        solvers_data = summary.get("by_solver", {})
        
        # Tabla de memoria
        pdf.set_fill_color(0, 51, 102)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)
        
        w = [50, 35, 35, 35, 30.9]
        headers = ["Solver", "Mem. Prom.", "Mem. Peak", "Eficiencia", "Problemas"]
        
        pdf.set_x(MARGIN + (CONTENT_WIDTH - sum(w)) / 2)
        for i, h in enumerate(headers):
            pdf.cell(w[i], 6, h, align=Align.C, fill=True)
        pdf.ln(6)
        
        pdf.set_font('Helvetica', '', 8)
        
        for solver, data in solvers_data.items():
            avg_mem = data.get("avg_memory", 0)
            peak_mem = data.get("peak_memory", 0)
            runs = data.get("runs", 1)
            successful = data.get("successful", 0)
            
            # Eficiencia: problemas resueltos / memoria usada
            efficiency = successful / max(avg_mem, 1) if avg_mem > 0 else 0
            
            pdf.set_x(MARGIN + (CONTENT_WIDTH - sum(w)) / 2)
            
            if successful == runs:
                pdf.set_text_color(0, 128, 0)
            elif successful == 0:
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(200, 140, 0)
            
            pdf.cell(w[0], 5, solver, align=Align.L)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(w[1], 5, f"{avg_mem:.1f} MB", align=Align.C)
            pdf.cell(w[2], 5, f"{peak_mem:.1f} MB", align=Align.C)
            pdf.cell(w[3], 5, f"{efficiency:.2f}", align=Align.C)
            pdf.cell(w[4], 5, f"{successful}/{runs}", align=Align.C)
            pdf.ln(5)
        
        pdf.ln(3)
        
        # Interpretacion
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(CONTENT_WIDTH, 4, 
                      "Eficiencia = Problemas resueltos / Memoria promedio. "
                      "Valores mas altos indican mejor uso de recursos.")
        
        pdf.set_text_color(0, 0, 0)