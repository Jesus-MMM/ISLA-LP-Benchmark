"""
Modulo de analisis para problemas de programacion lineal.
Reporte academico profesional usando fpdf2.
"""

from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any
import tempfile
import os
import platform
import sys
import math

from fpdf import FPDF
from fpdf.enums import Align, XPos, YPos

from ..core import LinearProblem, LinearConstraint, Solution

try:
    from .sensitivity import SensitivityAnalysis as _SensitivityAnalysis
    SENSITIVITY_ANALYSIS_AVAILABLE = True
except ImportError:
    SENSITIVITY_ANALYSIS_AVAILABLE = False
    _SensitivityAnalysis = None


PAGE_WIDTH = 215.9
PAGE_HEIGHT = 279.4
MARGIN = 15
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN


@dataclass
class ExecutionTimes:
    parse_time: float = 0.0
    build_time: float = 0.0
    solve_time: float = 0.0
    visualize_time: float = 0.0
    pdf_time: float = 0.0
    total_time: float = 0.0


class LPAnalysis:
    """Genera reportes academicos profesionales para problemas de programacion lineal."""

    def __init__(self, problem: LinearProblem, solution: Solution, 
                 times: Optional[ExecutionTimes] = None,
                 system_info: Optional[Dict] = None,
                 solver_name: str = "gurobi",
                 sensitivity: Optional[Any] = None):
        self.problem = problem
        self.solution = solution
        self.times = times or ExecutionTimes()
        self.system_info = system_info if system_info is not None else {}
        self.solver_name = solver_name
        self.sensitivity = sensitivity or getattr(self.solution, 'sensitivity', None)
        self.page_count = 0

    def generate_pdf(self, output_path: str) -> None:
        """Genera un reporte academico completo."""
        pdf = ReporteAcademico()
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Pagina 1: Portada
        pdf.add_page()
        self.page_count += 1
        self._build_portada(pdf)
        
        # Pagina 2: Resumen ejecutivo y detalles tecnicos
        pdf.add_page()
        self.page_count += 1
        self._build_header(pdf)
        self._build_resumen_ejecutivo(pdf)
        self._build_detalles_tecnicos(pdf)
        
        # Pagina 3: Datos del problema
        pdf.add_page()
        self.page_count += 1
        self._build_header(pdf)
        self._build_datos_problema(pdf)
        self._build_funcion_objetivo(pdf)
        self._build_restricciones_tabla(pdf)
        
        # Pagina 4: Solucion optima y analisis
        pdf.add_page()
        self.page_count += 1
        self._build_header(pdf)
        self._build_solucion_optima(pdf)
        self._build_holgura_dual(pdf)
        self._build_costos_reducidos(pdf)
        
        # Pagina 5: Validacion y configuracion
        pdf.add_page()
        self.page_count += 1
        self._build_header(pdf)
        self._build_validacion_modelo(pdf)
        self._build_configuracion_solver(pdf)
        
        # Pagina 6: Base optima y metricas numericas
        pdf.add_page()
        self.page_count += 1
        self._build_header(pdf)
        self._build_base_optima(pdf)
        self._build_metricas_numericas(pdf)
        
        # Pagina 7: Analisis de sensibilidad y grafico (si es 2D)
        if len(self.problem.variables) == 2:
            pdf.add_page()
            self.page_count += 1
            self._build_header(pdf)
            self._build_analisis_sensibilidad(pdf)
            self._build_grafico(pdf)
        else:
            pdf.add_page()
            self.page_count += 1
            self._build_header(pdf)
            self._build_analisis_sensibilidad(pdf)
        
        # Pagina 8: Log de progreso e interpretacion
        pdf.add_page()
        self.page_count += 1
        self._build_header(pdf)
        self._build_log_progreso(pdf)
        self._build_interpretacion_ejecutiva(pdf)
        
        # Pagina 9: Referencias teoricas
        pdf.add_page()
        self.page_count += 1
        self._build_header(pdf)
        self._build_referencias_teoricas(pdf)
        
        pdf.output(output_path)

    def _build_header(self, pdf: 'ReporteAcademico') -> None:
        """Construye el encabezado."""
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 7, "SOLUCION DE PROGRAMA LINEAL", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(2)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, f"Metodo Simplex - Solucionador con {self.solver_name.upper()}", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(3)
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(5)

    def _build_portada(self, pdf: 'ReporteAcademico') -> None:
        """Construye la portada del reporte."""
        pdf.set_font('Helvetica', 'B', 24)
        pdf.set_text_color(0, 51, 102)
        pdf.ln(40)
        pdf.cell(0, 12, "SOLUCION DE PROGRAMA LINEAL", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(10)
        pdf.set_font('Helvetica', 'I', 14)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, "Reporte Academico de Optimizacion", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(30)
        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(60, 60, 60)
        
        tipo = "Maximizacion" if self.problem.sense.lower() == "max" else "Minimizacion"
        pdf.cell(0, 8, f"Tipo de problema: {tipo}", align=Align.C, new_y=YPos.NEXT)
        pdf.ln(4)
        pdf.cell(0, 8, f"Numero de variables: {len(self.problem.variables)}", align=Align.C, new_y=YPos.NEXT)
        pdf.ln(4)
        pdf.cell(0, 8, f"Numero de restricciones: {len(self.problem.constraints)}", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(30)
        pdf.set_font('Helvetica', 'I', 11)
        pdf.set_text_color(100, 100, 100)
        fecha = datetime.now().strftime("%d de %B de %Y")
        pdf.cell(0, 8, f"Fecha de generacion: {fecha}", align=Align.C, new_y=YPos.NEXT)
        
        pdf.ln(10)
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(1.0)
        pdf.line(MARGIN + 30, pdf.get_y(), PAGE_WIDTH - MARGIN - 30, pdf.get_y())
        pdf.set_text_color(0, 0, 0)

    def _build_resumen_ejecutivo(self, pdf: 'ReporteAcademico') -> None:
        """Construye el resumen ejecutivo."""
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "Resumen Ejecutivo", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(2)
        
        col_width = CONTENT_WIDTH / 3
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.set_x(MARGIN)
        pdf.cell(col_width, 5, f"Tipo: {'MAX' if self.problem.sense.lower() == 'max' else 'MIN'}")
        pdf.cell(col_width, 5, f"Variables: {len(self.problem.variables)}")
        pdf.cell(col_width, 5, f"Restricciones: {len(self.problem.constraints)}")
        pdf.ln(5)
        
        pdf.set_x(MARGIN)
        pdf.cell(col_width, 5, "Estado:")
        if self.solution.status == 'OPTIMAL':
            pdf.set_text_color(0, 128, 0)
            pdf.cell(col_width, 5, "OPTIMA")
        else:
            pdf.set_text_color(200, 0, 0)
            pdf.cell(col_width, 5, self.solution.status)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        pdf.set_x(MARGIN)
        pdf.cell(col_width, 5, "Valor optimo:")
        pdf.set_text_color(0, 0, 150)
        if self.solution.objective_value is not None:
            pdf.cell(col_width * 2, 5, f"Z* = {self.solution.objective_value:,.4f}")
        else:
            pdf.cell(col_width * 2, 5, "No disponible")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

    def _build_detalles_tecnicos(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de detalles tecnicos."""
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "Informacion del Sistema", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(2)
        
        p = self.system_info.get("platform", {})
        
        half_width = CONTENT_WIDTH / 2
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(60, 60, 60)
        pdf.set_x(MARGIN)
        pdf.cell(half_width, 4, f"Solver: {self.solver_name}")
        pdf.cell(half_width, 4, f"Python: {p.get('python_version', sys.version.split()[0])}")
        pdf.ln(4)
        
        pdf.set_x(MARGIN)
        pdf.cell(half_width, 4, f"Sistema: {p.get('system', platform.system())} {p.get('release', platform.release())}")
        pdf.cell(half_width, 4, f"Procesador: {p.get('processor', platform.processor())}")
        pdf.ln(4)
        
        pdf.set_x(MARGIN)
        pdf.cell(half_width, 4, f"Arquitectura: {p.get('machine', platform.machine())}")
        pdf.cell(half_width, 4, f"Hostname: {self.system_info.get('hostname', platform.node())}")
        pdf.ln(4)
        
        pdf.set_x(MARGIN)
        pdf.cell(half_width, 4, f"Fecha: {self.system_info.get('timestamp', datetime.now().isoformat())[:19]}")
        pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
        self._build_analisis_tiempos(pdf)
    
    def _build_analisis_tiempos(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de analisis de tiempos."""
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 5, "Tiempos de Ejecucion", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        times_data = [
            ("Parsing", self.times.parse_time),
            ("Build", self.times.build_time),
            ("Solving", self.times.solve_time),
            ("Visualizacion", self.times.visualize_time),
            ("PDF", self.times.pdf_time),
        ]
        
        col1 = CONTENT_WIDTH * 0.65
        col2 = CONTENT_WIDTH * 0.35
        
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col1, 5, "Etapa", align=Align.L)
        pdf.cell(col2, 5, "Tiempo (s)", align=Align.R)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        pdf.set_x(MARGIN)
        
        for stage, time_val in times_data:
            if time_val > 0:
                pdf.cell(col1, 4, stage)
                pdf.cell(col2, 4, f"{time_val:.4f}", align=Align.R)
                pdf.ln(4)
                pdf.set_x(MARGIN)
        
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_draw_color(0, 51, 102)
        pdf.line(MARGIN + 3, pdf.get_y(), PAGE_WIDTH - MARGIN - 3, pdf.get_y())
        pdf.ln(2)
        
        pdf.set_x(MARGIN)
        pdf.cell(col1, 4, "TOTAL")
        pdf.cell(col2, 4, f"{self.times.total_time:.4f}", align=Align.R)
        pdf.ln(5)

    def _build_datos_problema(self, pdf: 'ReporteAcademico') -> None:
        """Construye la tabla de datos del problema."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "DATOS DEL PROBLEMA", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(2)
        
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5, "Variables:", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        col_widths = [CONTENT_WIDTH * 0.3, CONTENT_WIDTH * 0.35, CONTENT_WIDTH * 0.35]
        
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
        
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(col_widths[0], 5, "Variable", align=Align.C)
        pdf.cell(col_widths[1], 5, "Limite Inferior", align=Align.C)
        pdf.cell(col_widths[2], 5, "Limite Superior", align=Align.C)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        for var in self.problem.variables:
            bound = self.problem.bounds.get(var)
            lower = "0" if bound is None or bound.lower is None else str(bound.lower)
            upper = "Sin limite" if bound is None or bound.upper is None else str(bound.upper)
            
            pdf.cell(col_widths[0], 5, str(var), align=Align.C)
            pdf.cell(col_widths[1], 5, lower, align=Align.C)
            pdf.cell(col_widths[2], 5, upper[:15], align=Align.C)
            pdf.ln(5)
        
        pdf.ln(3)

    def _build_funcion_objetivo(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de funcion objetivo."""
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5, "Funcion Objetivo:", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        sense = "MAXIMIZAR" if self.problem.sense.lower() == "max" else "MINIMIZAR"
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 5, f"Tipo: {sense}", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        obj_str = self._format_objective()
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 102, 0)
        pdf.cell(10, 6, "Z =")
        pdf.cell(0, 6, obj_str, new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    def _build_restricciones_tabla(self, pdf: 'ReporteAcademico') -> None:
        """Construye la tabla de restricciones."""
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5, "Restricciones:", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        w = [CONTENT_WIDTH * 0.08, CONTENT_WIDTH * 0.52, CONTENT_WIDTH * 0.18, CONTENT_WIDTH * 0.22]
        
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
        
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w[0], 5, "#", align=Align.C)
        pdf.cell(w[1], 5, "Expresion", align=Align.C)
        pdf.cell(w[2], 5, "Tipo", align=Align.C)
        pdf.cell(w[3], 5, "RHS", align=Align.C)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        
        for i, c in enumerate(self.problem.constraints):
            cstr = self._format_constraint(c)
            if len(cstr) > 35:
                cstr = cstr[:32] + "..."
            
            pdf.cell(w[0], 5, str(i + 1), align=Align.C)
            pdf.cell(w[1], 5, cstr, align=Align.L)
            pdf.cell(w[2], 5, c.sense, align=Align.C)
            pdf.cell(w[3], 5, f"{c.rhs:.2f}", align=Align.R)
            pdf.ln(5)
        
        pdf.ln(3)

    def _build_solucion_optima(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de solucion optima."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "SOLUCION OPTIMA", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(2)
        
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(35, 5, "Estado: ", align=Align.L)
        
        if self.solution.status == 'OPTIMAL':
            pdf.set_text_color(0, 128, 0)
            pdf.cell(0, 5, "OPTIMA", new_x=XPos.LEFT, new_y=YPos.NEXT)
        else:
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, 5, self.solution.status, new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        if self.solution.objective_value is not None:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 0, 150)
            pdf.cell(25, 6, "Valor optimo:")
            pdf.cell(0, 6, f"Z* = {self.solution.objective_value:,.4f}", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        if self.solution.iterations > 0 or self.solution.nodes > 0:
            pdf.ln(2)
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(60, 60, 60)
            if self.solution.iterations > 0:
                pdf.cell(0, 4, f"Iteraciones: {self.solution.iterations}", new_x=XPos.LEFT, new_y=YPos.NEXT)
            if self.solution.nodes > 0:
                pdf.cell(0, 4, f"Nodos explorados: {self.solution.nodes}", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.ln(2)
        
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 5, "Valores de las variables:", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        w = [CONTENT_WIDTH * 0.35, CONTENT_WIDTH * 0.35, CONTENT_WIDTH * 0.30]
        
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
        
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w[0], 5, "Variable", align=Align.C)
        pdf.cell(w[1], 5, "Valor Optimo", align=Align.C)
        pdf.cell(w[2], 5, "Costo Reducido", align=Align.C)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        for var, value in self.solution.variables.items():
            reduced_cost = self.solution.reduced_costs.get(var, 0) if self.solution.reduced_costs else 0
            pdf.cell(w[0], 5, str(var), align=Align.C)
            pdf.cell(w[1], 5, f"{value:.4f}", align=Align.C)
            pdf.cell(w[2], 5, f"{reduced_cost:.4f}", align=Align.C)
            pdf.ln(5)
        
        pdf.ln(3)

    def _build_holgura_dual(self, pdf: 'ReporteAcademico') -> None:
        """Construye el analisis de holgura y precios sombra."""
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 5, "ANALISIS DE HOLGURA Y PRECIOS SOMBRA", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, "Holgura: recurso no utilizado. Precio Sombra: valor marginal de relajar la restriccion.")
        pdf.ln(2)
        
        w = [CONTENT_WIDTH * 0.06, CONTENT_WIDTH * 0.32, CONTENT_WIDTH * 0.14, CONTENT_WIDTH * 0.12, CONTENT_WIDTH * 0.18, CONTENT_WIDTH * 0.18]
        
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
        
        pdf.set_font('Helvetica', 'B', 6)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w[0], 5, "#", align=Align.C)
        pdf.cell(w[1], 5, "Restriccion", align=Align.C)
        pdf.cell(w[2], 5, "Lado Der.", align=Align.C)
        pdf.cell(w[3], 5, "Sentido", align=Align.C)
        pdf.cell(w[4], 5, "Holgura", align=Align.C)
        pdf.cell(w[5], 5, "Precio Sombra", align=Align.C)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 6)
        
        for i, c in enumerate(self.problem.constraints):
            cstr = self._format_constraint_short(c)
            if len(cstr) > 22:
                cstr = cstr[:19] + "..."
            
            if self.solution.variables:
                value = sum(
                    c.coefficients.get(var, 0) * self.solution.variables.get(var, 0)
                    for var in self.problem.variables
                )
                
                if c.sense == '<=':
                    slack = c.rhs - value
                elif c.sense == '>=':
                    slack = value - c.rhs
                else:
                    slack = 0
                
                if abs(slack) < 1e-6:
                    pdf.set_text_color(200, 0, 0)
                elif slack > 0:
                    pdf.set_text_color(0, 128, 0)
                else:
                    pdf.set_text_color(200, 0, 0)
                
                dual_value = self.solution.dual_values.get(f"c{i+1}", 0) if self.solution.dual_values else 0
                slack_str = f"{slack:.2f}"
                dual_str = f"{dual_value:.2f}"
            else:
                slack_str = "-"
                dual_str = "-"
                pdf.set_text_color(100, 100, 100)
            
            pdf.cell(w[0], 4, str(i + 1), align=Align.C)
            pdf.cell(w[1], 4, cstr, align=Align.L)
            pdf.cell(w[2], 4, f"{c.rhs:.1f}", align=Align.R)
            pdf.cell(w[3], 4, c.sense, align=Align.C)
            pdf.cell(w[4], 4, slack_str, align=Align.R)
            pdf.cell(w[5], 4, dual_str, align=Align.R)
            pdf.ln(4)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    def _build_costos_reducidos(self, pdf: 'ReporteAcademico') -> None:
        """Construye el analisis de costos reducidos."""
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 5, "COSTOS REDUCIDOS", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(2)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, "Costo Reducido: cantidad que el objetivo mejoraria si la variable aumenta en una unidad. Variables con costo reducido = 0 estan en su valor optimo.")
        pdf.ln(2)
        
        if self.solution.reduced_costs:
            w = [CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.25]
            
            pdf.set_fill_color(0, 51, 102)
            pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
            
            pdf.set_font('Helvetica', 'B', 7)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(w[0], 5, "Variable", align=Align.C)
            pdf.cell(w[1], 5, "Valor Optimo", align=Align.C)
            pdf.cell(w[2], 5, "Costo Reducido", align=Align.C)
            pdf.cell(w[3], 5, "Interpretacion", align=Align.C)
            pdf.ln(5)
            
            pdf.set_font('Helvetica', '', 7)
            
            for var, value in self.solution.variables.items():
                reduced_cost = self.solution.reduced_costs.get(var, 0)
                
                if abs(reduced_cost) > 1e-6:
                    interp = "En limite"
                else:
                    interp = "Optima"
                
                pdf.cell(w[0], 4, var, align=Align.C)
                pdf.cell(w[1], 4, f"{value:.4f}", align=Align.R)
                pdf.cell(w[2], 4, f"{reduced_cost:.4f}", align=Align.R)
                pdf.cell(w[3], 4, interp, align=Align.C)
                pdf.ln(4)
        else:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, "Costos reducidos no disponibles.", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    def _build_analisis_sensibilidad(self, pdf: 'ReporteAcademico') -> None:
        """Construye el analisis de sensibilidad con tablas de rangos."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "ANALISIS DE SENSIBILIDAD", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(2)
        
        sens = self.sensitivity
        if sens is None:
            sens = getattr(self.solution, 'sensitivity', None)
        
        if sens is not None and (sens.objective_ranges or sens.rhs_ranges or sens.bound_ranges):
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(CONTENT_WIDTH, 4,
                "Rangos de variacion de los coeficientes manteniendo la base optima:")
            pdf.ln(2)
            if sens.objective_ranges:
                self._build_tabla_rangos_objetivo(pdf, sens.objective_ranges)
            if sens.rhs_ranges:
                pdf.ln(1)
                self._build_tabla_rangos_rhs(pdf, sens.rhs_ranges)
            if sens.bound_ranges:
                pdf.ln(1)
                self._build_tabla_rangos_limites(pdf, sens.bound_ranges)
        else:
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(CONTENT_WIDTH, 4,
                "El analisis de sensibilidad muestra como cambios en los parametros "
                "afectan la solucion optima. No se dispone de datos numericos de "
                "sensibilidad para este problema.")
            pdf.ln(3)
        
        self._build_interpretacion_sensibilidad(pdf)
    
    def _build_tabla_rangos_objetivo(
        self, pdf: 'ReporteAcademico', ranges: list
    ) -> None:
        """Tabla de rangos de coeficientes objetivo."""
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 5, "Rangos de Coeficientes Objetivo", new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.ln(1)
        
        w = [0.28, 0.18, 0.18, 0.18, 0.18]
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w[0] * CONTENT_WIDTH, 5, "Variable", align=Align.C)
        pdf.cell(w[1] * CONTENT_WIDTH, 5, "Actual", align=Align.C)
        pdf.cell(w[2] * CONTENT_WIDTH, 5, "Minimo", align=Align.C)
        pdf.cell(w[3] * CONTENT_WIDTH, 5, "Maximo", align=Align.C)
        pdf.cell(w[4] * CONTENT_WIDTH, 5, "Costo Red.", align=Align.C)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        for r in ranges:
            lower_str = f"{r.lower:.4f}" if r.lower is not None else "-inf"
            upper_str = f"{r.upper:.4f}" if r.upper is not None else "+inf"
            rc_str = f"{r.reduced_cost:.4f}" if r.reduced_cost is not None else "-"
            name = str(r.name)[:20]
            pdf.cell(w[0] * CONTENT_WIDTH, 4, name, align=Align.C)
            pdf.cell(w[1] * CONTENT_WIDTH, 4, f"{r.current:.4f}", align=Align.C)
            pdf.cell(w[2] * CONTENT_WIDTH, 4, lower_str, align=Align.C)
            pdf.cell(w[3] * CONTENT_WIDTH, 4, upper_str, align=Align.C)
            pdf.cell(w[4] * CONTENT_WIDTH, 4, rc_str, align=Align.C)
            pdf.ln(4)
        
        pdf.ln(1)
    
    def _build_tabla_rangos_rhs(
        self, pdf: 'ReporteAcademico', ranges: list
    ) -> None:
        """Tabla de rangos de lados derechos (RHS)."""
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 5, "Rangos de Lados Derechos (RHS)", new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.ln(1)
        
        w = [0.28, 0.18, 0.18, 0.18, 0.18]
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w[0] * CONTENT_WIDTH, 5, "Restriccion", align=Align.C)
        pdf.cell(w[1] * CONTENT_WIDTH, 5, "Actual", align=Align.C)
        pdf.cell(w[2] * CONTENT_WIDTH, 5, "Minimo", align=Align.C)
        pdf.cell(w[3] * CONTENT_WIDTH, 5, "Maximo", align=Align.C)
        pdf.cell(w[4] * CONTENT_WIDTH, 5, "Precio Sombra", align=Align.C)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        for r in ranges:
            lower_str = f"{r.lower:.4f}" if r.lower is not None else "-inf"
            upper_str = f"{r.upper:.4f}" if r.upper is not None else "+inf"
            dual_str = f"{r.dual_value:.4f}" if r.dual_value is not None else "-"
            name = str(r.name)[:20]
            pdf.cell(w[0] * CONTENT_WIDTH, 4, name, align=Align.C)
            pdf.cell(w[1] * CONTENT_WIDTH, 4, f"{r.current:.4f}", align=Align.C)
            pdf.cell(w[2] * CONTENT_WIDTH, 4, lower_str, align=Align.C)
            pdf.cell(w[3] * CONTENT_WIDTH, 4, upper_str, align=Align.C)
            pdf.cell(w[4] * CONTENT_WIDTH, 4, dual_str, align=Align.C)
            pdf.ln(4)
        
        pdf.ln(1)
    
    def _build_tabla_rangos_limites(
        self, pdf: 'ReporteAcademico', ranges: list
    ) -> None:
        """Tabla de rangos de limites de variables."""
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 5, "Rangos de Limites de Variables", new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.ln(1)
        
        w = [0.28, 0.24, 0.24, 0.24]
        pdf.set_fill_color(0, 51, 102)
        pdf.rect(MARGIN, pdf.get_y(), CONTENT_WIDTH, 5, 'F')
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w[0] * CONTENT_WIDTH, 5, "Variable", align=Align.C)
        pdf.cell(w[1] * CONTENT_WIDTH, 5, "Actual", align=Align.C)
        pdf.cell(w[2] * CONTENT_WIDTH, 5, "Minimo", align=Align.C)
        pdf.cell(w[3] * CONTENT_WIDTH, 5, "Maximo", align=Align.C)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        for r in ranges:
            lower_str = f"{r.lower:.4f}" if r.lower is not None else "-inf"
            upper_str = f"{r.upper:.4f}" if r.upper is not None else "+inf"
            name = str(r.name)[:20]
            pdf.cell(w[0] * CONTENT_WIDTH, 4, name, align=Align.C)
            pdf.cell(w[1] * CONTENT_WIDTH, 4, f"{r.current:.4f}", align=Align.C)
            pdf.cell(w[2] * CONTENT_WIDTH, 4, lower_str, align=Align.C)
            pdf.cell(w[3] * CONTENT_WIDTH, 4, upper_str, align=Align.C)
            pdf.ln(4)
        
        pdf.ln(1)
    
    def _build_interpretacion_sensibilidad(self, pdf: 'ReporteAcademico') -> None:
        """Construye la interpretacion del analisis de sensibilidad."""
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 5, "Interpretacion:", new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.ln(1)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        interpretations = [
            "Restricciones ACTIVAS (holgura = 0): Utilizan completamente el recurso.",
            "Restricciones NO ACTIVAS (holgura > 0): Recurso disponible sin usar.",
            "Precio Sombra > 0: Aumentar el RHS mejora el valor objetivo.",
            "Precio Sombra = 0: La restriccion no limita el problema.",
        ]
        for item in interpretations:
            pdf.cell(5, 4, "-")
            pdf.cell(0, 4, item, new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.ln(3)

    def _build_grafico(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion del grafico de region factible."""
        pdf.ln(5)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "REGION FACTIBLE", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(3)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 5, f"Grafico para variables: {self.problem.variables[0]}, {self.problem.variables[1]}", 
                 new_x=XPos.LEFT, new_y=YPos.NEXT)
        pdf.ln(2)
        
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            from matplotlib.patches import Polygon
            from matplotlib.colors import TABLEAU_COLORS as TAB10_COLORS
            
            var_x = self.problem.variables[0]
            var_y = self.problem.variables[1]
            
            x_min, x_max, y_min, y_max = self._calculate_plot_range(var_x, var_y)
            
            fig, ax = plt.subplots(figsize=(5, 4))
            
            colors = list(TAB10_COLORS)
            x_vals = np.linspace(x_min, x_max, 200)
            
            all_constraints = self._get_all_constraints_with_bounds(var_x, var_y)
            
            for i, c in enumerate(self.problem.constraints):
                a = c.coefficients.get(var_x, 0)
                b = c.coefficients.get(var_y, 0)
                rhs = c.rhs
                
                sense_label = c.sense
                label = f"R{i+1}: {a:.1f}{var_x} {sense_label} {rhs:.1f}"
                
                linestyle = '--' if c.sense == ">=" else ('-' if c.sense == "<=" else ':')
                if abs(b) < 1e-10 and abs(a) > 1e-10:
                    x_const = rhs / a
                    y_range = np.linspace(y_min, y_max, 200)
                    x_line = np.full_like(y_range, x_const)
                    ax.plot(x_line, y_range, color=colors[i % len(colors)], 
                            linewidth=2, linestyle=linestyle, label=label)
                else:
                    y_vals = (rhs - a * x_vals) / b
                    valid = np.isfinite(y_vals)
                    ax.plot(x_vals[valid], y_vals[valid], color=colors[i % len(colors)], 
                            linewidth=2, linestyle=linestyle, label=label)
            
            vertices = self._find_feasible_vertices(all_constraints, var_x, var_y)
            
            if len(vertices) >= 3:
                cx = sum(v[0] for v in vertices) / len(vertices)
                cy = sum(v[1] for v in vertices) / len(vertices)
                vertices_sorted = sorted(vertices, key=lambda v: math.atan2(v[1] - cy, v[0] - cx))
                
                polygon = Polygon(vertices_sorted, closed=True, alpha=0.3, 
                                 facecolor='#90EE90', edgecolor='#228B22', linewidth=2)
                ax.add_patch(polygon)
            elif len(vertices) == 2:
                ax.fill([v[0] for v in vertices] + [vertices[0][0]], 
                       [v[1] for v in vertices] + [vertices[0][1]], 
                       alpha=0.3, facecolor='#90EE90', edgecolor='#228B22', linewidth=2)
            
            linestyle_gray = ':'
            for i, c in enumerate(all_constraints):
                if c not in self.problem.constraints:
                    a = c.coefficients.get(var_x, 0)
                    b = c.coefficients.get(var_y, 0)
                    rhs = c.rhs
                    
                    if abs(b) < 1e-10 and abs(a) > 1e-10:
                        x_const = rhs / a
                        y_range = np.linspace(y_min, y_max, 200)
                        x_line = np.full_like(y_range, x_const)
                        ax.plot(x_line, y_range, color='gray', linewidth=1.5, 
                                linestyle=linestyle_gray, alpha=0.6)
                    elif abs(a) < 1e-10 and abs(b) > 1e-10:
                        y_const = rhs / b
                        ax.axhline(y_const, color='gray', linewidth=1.5, 
                                  linestyle=linestyle_gray, alpha=0.6)
            
            if self.solution.variables:
                x = self.solution.variables.get(var_x, 0)
                y = self.solution.variables.get(var_y, 0)
                ax.scatter([x], [y], color='red', s=300, zorder=10, marker='*', 
                          edgecolors='black', linewidths=1.5)
                ax.annotate(f'Optimo\n({x:.2f}, {y:.2f})', (x, y), 
                           textcoords="offset points", xytext=(15, 15), fontsize=10,
                           fontweight='bold', color='darkred',
                           arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))
                
                obj = self.problem.objective
                a = obj.get(var_x, 0)
                b = obj.get(var_y, 0)
                
                if abs(b) > 1e-10:
                    opt_val = a * x + b * y
                    y_obj = (opt_val - a * x_vals) / b
                    valid = np.isfinite(y_obj) & (y_obj >= y_min) & (y_obj <= y_max)
                    ax.plot(x_vals[valid], y_obj[valid], 'b--', alpha=0.6, linewidth=1.5,
                           label=f'Funcion objetivo (Z={opt_val:.2f})')
            
            padding_x = (x_max - x_min) * 0.1
            padding_y = (y_max - y_min) * 0.1
            ax.set_xlim(x_min - padding_x, x_max + padding_x)
            ax.set_ylim(y_min - padding_y, y_max + padding_y)
            
            ax.set_xlabel(var_x, fontsize=12, fontweight='bold')
            ax.set_ylabel(var_y, fontsize=12, fontweight='bold')
            ax.set_title(f'Region Factible - {self.problem.sense.upper()}', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.axhline(y=0, color='black', linewidth=1)
            ax.axvline(x=0, color='black', linewidth=1)
            ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                plt.savefig(tmp.name, dpi=300, bbox_inches='tight', facecolor='white')
                tmp_path = tmp.name
            
            plt.close()
            
            if os.path.exists(tmp_path):
                pdf.ln(5)
                # Calcular ancho proporcional respetando margenes
                img_width = min(CONTENT_WIDTH - 30, 120)
                x_pos = MARGIN + (CONTENT_WIDTH - img_width) / 2
                if pdf.get_y() + 80 > 279.4 - 15:  # Check if image fits
                    pdf.add_page()
                    self._build_header(pdf)
                    pdf.ln(5)
                pdf.image(tmp_path, x=x_pos, w=img_width)
                os.unlink(tmp_path)
                
        except Exception as e:
            pdf.ln(3)
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(150, 0, 0)
            pdf.cell(0, 5, f"No se pudo generar el grafico: {str(e)}", 
                     new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)

    def _get_all_constraints_with_bounds(self, var_x: str, var_y: str) -> list:
        """Obtiene todas las restricciones incluyendo bounds."""
        constraints = list(self.problem.constraints)
        bounds = self.problem.bounds
        
        x_bound = bounds.get(var_x)
        y_bound = bounds.get(var_y)
        
        if x_bound is None:
            constraints.append(LinearConstraint(coefficients={var_x: 1}, rhs=0, sense=">="))
        else:
            if x_bound.lower is not None:
                constraints.append(LinearConstraint(coefficients={var_x: 1}, rhs=x_bound.lower, sense=">="))
            if x_bound.upper is not None:
                constraints.append(LinearConstraint(coefficients={var_x: 1}, rhs=x_bound.upper, sense="<="))
        
        if y_bound is None:
            constraints.append(LinearConstraint(coefficients={var_y: 1}, rhs=0, sense=">="))
        else:
            if y_bound.lower is not None:
                constraints.append(LinearConstraint(coefficients={var_y: 1}, rhs=y_bound.lower, sense=">="))
            if y_bound.upper is not None:
                constraints.append(LinearConstraint(coefficients={var_y: 1}, rhs=y_bound.upper, sense="<="))
        
        return constraints

    def _calculate_plot_range(self, var_x: str, var_y: str) -> tuple:
        """Calcula el rango de la grafica."""
        x_min, x_max = -5, 50
        y_min, y_max = -5, 50
        
        all_constraints = self._get_all_constraints_with_bounds(var_x, var_y)
        
        for c in all_constraints:
            a = c.coefficients.get(var_x, 0)
            b = c.coefficients.get(var_y, 0)
            rhs = c.rhs
            
            if abs(b) < 1e-10 and abs(a) > 1e-10:
                val = rhs / a
                if val > 0:
                    x_max = max(x_max, val * 1.3)
                else:
                    x_min = min(x_min, val * 1.3)
            elif abs(a) < 1e-10 and abs(b) > 1e-10:
                val = rhs / b
                if val > 0:
                    y_max = max(y_max, val * 1.3)
                else:
                    y_min = min(y_min, val * 1.3)
            else:
                if abs(b) > 1e-10:
                    x_intercept = rhs / b
                    if x_intercept > 0:
                        x_max = max(x_max, x_intercept * 1.3)
                    else:
                        x_min = min(x_min, x_intercept * 1.3)
                if abs(a) > 1e-10:
                    y_intercept = rhs / a
                    if y_intercept > 0:
                        y_max = max(y_max, y_intercept * 1.3)
                    else:
                        y_min = min(y_min, y_intercept * 1.3)
        
        if self.solution and self.solution.variables:
            sol_x = self.solution.variables.get(var_x, 0)
            sol_y = self.solution.variables.get(var_y, 0)
            
            x_max = max(x_max, sol_x * 1.5, 10)
            y_max = max(y_max, sol_y * 1.5, 10)
            
            if sol_x < 0:
                x_min = min(x_min, sol_x * 1.5)
            if sol_y < 0:
                y_min = min(y_min, sol_y * 1.5)
        
        x_range = x_max - x_min
        if x_range < 10:
            mid = (x_max + x_min) / 2
            x_min = mid - 5
            x_max = mid + 5
        
        y_range = y_max - y_min
        if y_range < 10:
            mid = (y_max + y_min) / 2
            y_min = mid - 5
            y_max = mid + 5
        
        return x_min, x_max, y_min, y_max

    def _find_feasible_vertices(self, constraints: list, var_x: str, var_y: str) -> list:
        """Encuentra vertices de la region factible."""
        vertices = []
        
        for i, c1 in enumerate(constraints):
            for c2 in constraints[i+1:]:
                intersection = self._find_intersection(c1, c2, var_x, var_y)
                if intersection:
                    x, y = intersection
                    if self._is_point_feasible(x, y, constraints, var_x, var_y):
                        if not any(math.isclose(x, v[0], abs_tol=1e-8) and 
                                  math.isclose(y, v[1], abs_tol=1e-8) for v in vertices):
                            vertices.append((x, y))
        
        if self._is_point_feasible(0, 0, constraints, var_x, var_y):
            if not any(math.isclose(0, v[0], abs_tol=1e-8) and 
                      math.isclose(0, v[1], abs_tol=1e-8) for v in vertices):
                vertices.append((0, 0))
        
        return vertices

    def _find_intersection(self, c1, c2, var_x, var_y):
        """Encuentra la interseccion de dos restricciones."""
        a1 = c1.coefficients.get(var_x, 0)
        b1 = c1.coefficients.get(var_y, 0)
        r1 = c1.rhs
        
        a2 = c2.coefficients.get(var_x, 0)
        b2 = c2.coefficients.get(var_y, 0)
        r2 = c2.rhs
        
        det = a1 * b2 - a2 * b1
        
        if abs(det) < 1e-10:
            return None
        
        x = (r1 * b2 - r2 * b1) / det
        y = (a1 * r2 - a2 * r1) / det
        
        return (x, y)

    def _is_point_feasible(self, x, y, constraints, var_x, var_y) -> bool:
        """Verifica si un punto es factible."""
        for c in constraints:
            value = c.coefficients.get(var_x, 0) * x + c.coefficients.get(var_y, 0) * y
            
            if c.sense == "<=":
                if value > c.rhs + 1e-9:
                    return False
            elif c.sense == ">=":
                if value < c.rhs - 1e-9:
                    return False
            elif c.sense == "=":
                if abs(value - c.rhs) > 1e-9:
                    return False
        
        return True

    def _format_objective(self) -> str:
        """Formatea la funcion objetivo."""
        terms = []
        for var in self.problem.variables:
            coeff = self.problem.objective.get(var, 0)
            if coeff != 0:
                terms.append(f"{coeff:+g}{var}")
        obj_str = " ".join(terms)
        if obj_str.startswith("+"):
            obj_str = obj_str[1:]
        return obj_str

    def _format_constraint(self, c) -> str:
        """Formatea una restriccion."""
        terms = []
        for var in self.problem.variables:
            coeff = c.coefficients.get(var, 0)
            if coeff != 0:
                terms.append(f"{coeff:+g}{var}")
        constraint_str = " ".join(terms)
        if constraint_str.startswith("+"):
            constraint_str = constraint_str[1:]
        return f"{constraint_str} {c.sense} {c.rhs}"

    def _format_constraint_short(self, c) -> str:
        """Formatea una restriccion de forma corta."""
        terms = []
        for var in self.problem.variables:
            coeff = c.coefficients.get(var, 0)
            if coeff != 0:
                terms.append(f"{coeff:+g}{var}")
        constraint_str = " ".join(terms)
        if constraint_str.startswith("+"):
            constraint_str = constraint_str[1:]
        return constraint_str

    def _build_validacion_modelo(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de validacion del modelo."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "VALIDACION DEL MODELO", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(3)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, "Verificacion de la integridad del modelo: limites de variables, consistencia de restricciones y factibilidad.")
        pdf.ln(3)
        
        # Validacion basica del modelo
        is_valid = True
        errors = []
        warnings = []
        
        # Check basic problem structure
        if not self.problem.variables:
            is_valid = False
            errors.append("No variables defined")
        if not self.problem.constraints:
            warnings.append("No constraints defined")
        
        is_valid = is_valid and len(errors) == 0
        
        try:
            pdf.set_font('Helvetica', 'B', 9)
            if is_valid:
                pdf.set_text_color(0, 128, 0)
                pdf.cell(0, 5, "Modelo VALIDO", new_x=XPos.LEFT, new_y=YPos.NEXT)
            else:
                pdf.set_text_color(200, 0, 0)
                pdf.cell(0, 5, "Modelo CON ERRORES", new_x=XPos.LEFT, new_y=YPos.NEXT)
            
            pdf.set_font('Helvetica', '', 7)
            pdf.set_text_color(0, 0, 0)
            
            if errors:
                pdf.ln(2)
                pdf.set_text_color(200, 0, 0)
                pdf.cell(0, 4, "Errores encontrados:", new_x=XPos.LEFT, new_y=YPos.NEXT)
                for err in errors[:5]:
                    pdf.cell(5, 4, "-")
                    pdf.cell(0, 4, err[:60], new_x=XPos.LEFT, new_y=YPos.NEXT)
            
            if warnings:
                pdf.ln(2)
                pdf.set_text_color(200, 140, 0)
                pdf.cell(0, 4, "Advertencias:", new_x=XPos.LEFT, new_y=YPos.NEXT)
                for warn in warnings[:5]:
                    pdf.cell(5, 4, "-")
                    pdf.cell(0, 4, warn[:60], new_x=XPos.LEFT, new_y=YPos.NEXT)
        except Exception:
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, "Error en validacion", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    def _build_configuracion_solver(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de configuracion del solver."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "CONFIGURACION DEL SOLVER", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(3)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
        config_data = [
            ("Solver", self.solver_name.upper()),
            ("Sentido", "Maximizacion" if self.problem.sense.lower() == "max" else "Minimizacion"),
            ("Variables", str(len(self.problem.variables))),
            ("Restricciones", str(len(self.problem.constraints))),
        ]
        
        for label, value in config_data:
            pdf.set_x(MARGIN + 5)
            pdf.set_font('Helvetica', '', 8)
            pdf.cell(40, 5, f"{label}:")
            pdf.set_font('Helvetica', 'B', 8)
            pdf.cell(0, 5, value, new_x=XPos.LEFT, new_y=YPos.NEXT)
            pdf.set_x(MARGIN)
        
        pdf.ln(3)

    def _build_base_optima(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de base optima."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "BASE OPTIMA (VARIABLES BASICAS)", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(3)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, "Variables en la base: aquellas con valor > 0 en la solucion optima. Variables no-basicas: valor = 0.")
        pdf.ln(3)
        
        w = [CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.25]
        
        pdf.set_fill_color(0, 51, 102)
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w[0], 5, "Variable", align=Align.C, fill=True)
        pdf.cell(w[1], 5, "Valor", align=Align.C, fill=True)
        pdf.cell(w[2], 5, "Estado", align=Align.C, fill=True)
        pdf.cell(w[3], 5, "Costo Red.", align=Align.C, fill=True)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        
        for var, value in self.solution.variables.items():
            pdf.cell(w[0], 4, str(var), align=Align.C)
            pdf.cell(w[1], 4, f"{value:.4f}", align=Align.C)
            
            if abs(value) > 1e-6:
                pdf.set_text_color(0, 128, 0)
                pdf.cell(w[2], 4, "BASICA", align=Align.C)
                pdf.set_text_color(0, 0, 0)
            else:
                pdf.cell(w[2], 4, "NO BASICA", align=Align.C)
            
            reduced_cost = self.solution.reduced_costs.get(var, 0) if self.solution.reduced_costs else 0
            pdf.cell(w[3], 4, f"{reduced_cost:.4f}", align=Align.C)
            pdf.ln(4)
        
        pdf.ln(3)

    def _build_metricas_numericas(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de metricas numericas."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "METRICAS NUMERICAS", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(3)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(CONTENT_WIDTH, 4, "Calidad numerica: violaciones de limites, restricciones y numero de condicion de la matriz.")
        pdf.ln(3)
        
        col_w = CONTENT_WIDTH / 2
        
        pdf.set_x(MARGIN)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(col_w, 5, "Metrica", align=Align.L)
        pdf.cell(col_w, 5, "Valor", align=Align.R)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 8)
        
        nq = self.solution.numerical_quality
        max_bound_viol = nq.max_bound_viol if nq else 0
        max_constr_viol = nq.max_constraint_viol if nq else 0
        condition_num = nq.condition_number if nq else None
        
        metrics = [
            ("Violacion max. limites", f"{max_bound_viol:.2e}"),
            ("Violacion max. restricciones", f"{max_constr_viol:.2e}"),
            ("Numero de condicion", f"{condition_num:.2e}" if condition_num else "N/A"),
        ]
        
        pdf.set_x(MARGIN)
        for label, value in metrics:
            pdf.cell(col_w, 5, label)
            pdf.cell(col_w, 5, value, align=Align.R)
            pdf.ln(5)
            pdf.set_x(MARGIN)
        
        pdf.ln(3)

    def _build_log_progreso(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de log de progreso."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "LOG DE PROGRESO", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(3)
        
        progress_log = getattr(self.solution, 'progress_log', None)
        
        if progress_log and len(progress_log) > 0:
            pdf.set_font('Helvetica', '', 7)
            pdf.set_text_color(0, 0, 0)
            
            w = [CONTENT_WIDTH * 0.15, CONTENT_WIDTH * 0.25, CONTENT_WIDTH * 0.3, CONTENT_WIDTH * 0.3]
            
            pdf.set_fill_color(0, 51, 102)
            pdf.set_font('Helvetica', 'B', 6)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(w[0], 4, "Iter", align=Align.C, fill=True)
            pdf.cell(w[1], 4, "Objetivo", align=Align.C, fill=True)
            pdf.cell(w[2], 4, "Infactibilidad", align=Align.C, fill=True)
            pdf.cell(w[3], 4, "Tiempo", align=Align.C, fill=True)
            pdf.ln(4)
            
            pdf.set_font('Helvetica', '', 6)
            pdf.set_text_color(0, 0, 0)
            
            for point in progress_log[:20]:
                pdf.cell(w[0], 3, str(point.iteration), align=Align.C)
                pdf.cell(w[1], 3, f"{point.objective:.4f}", align=Align.C)
                pdf.cell(w[2], 3, f"{point.gap:.2e}", align=Align.C)
                pdf.cell(w[3], 3, f"{point.time:.2f}s", align=Align.C)
                pdf.ln(3)
        else:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, "No hay datos de progreso disponibles.", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    def _build_interpretacion_ejecutiva(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de interpretacion ejecutiva."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "INTERPRETACION EJECUTIVA", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(3)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)
        
        if self.solution.status == 'OPTIMAL':
            obj_val = self.solution.objective_value or 0
            sense = "maximizar" if self.problem.sense.lower() == "max" else "minimizar"
            
            texto = (
                f"La solucion optima permite {sense} el valor de la funcion objetivo "
                f"hasta {obj_val:,.2f}. "
                f"Se identificaron {len([v for v in self.solution.variables.values() if abs(v) > 1e-6])} "
                f"variables con valor positivo en la solucion optima. "
            )
            
            active_constraints = sum(1 for c in self.problem.constraints 
                                  if self._is_constraint_active(c))
            texto += f"Existen {active_constraints} restricciones activas que limitan la solucion."
            
            pdf.multi_cell(CONTENT_WIDTH, 5, texto)
        else:
            pdf.multi_cell(CONTENT_WIDTH, 5, 
                          f"El problema no tiene solucion optima. Estado: {self.solution.status}. "
                          "Verifique la formulacion del modelo.")
        
        pdf.ln(3)

    def _build_referencias_teoricas(self, pdf: 'ReporteAcademico') -> None:
        """Construye la seccion de referencias teoricas."""
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 6, "REFERENCIAS TEORICAS", new_x=XPos.LEFT, new_y=YPos.NEXT)
        
        pdf.set_draw_color(0, 51, 102)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(60, 60, 60)
        
        referencias = [
            "Metodo Simplex: Algoritmo iterativo para PL desarrollado por George Dantzig (1947).",
            "Holgura (Slack): Diferencia entre el valor de la restriccion y el lado derecho.",
            "Precio Sombra: Cambio en el objetivo por unidad de relajacion en el RHS.",
            "Costo Reducido: Costo marginal para que una variable no-basica entre a la base.",
            "Variables Basicas: Variables con valor > 0 en la solucion actual.",
            "Analisis de Sensibilidad: Estudio del rango de validez de los coeficientes.",
        ]
        
        for ref in referencias:
            pdf.cell(5, 5, "-")
            pdf.multi_cell(CONTENT_WIDTH - 5, 5, ref)
            pdf.ln(2)
        
        pdf.ln(3)

    def _is_constraint_active(self, c) -> bool:
        """Verifica si una restriccion es activa."""
        if not self.solution.variables:
            return False
        
        value = sum(c.coefficients.get(var, 0) * self.solution.variables.get(var, 0) 
                   for var in self.problem.variables)
        
        if c.sense == '<=':
            slack = c.rhs - value
        elif c.sense == '>=':
            slack = value - c.rhs
        else:
            slack = abs(value - c.rhs)
        
        return abs(slack) < 1e-6


class ReporteAcademico(FPDF):
    """Clase PDF academica personalizada."""
    
    def header(self):
        pass
    
    def footer(self):
        self.set_y(-15)
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_WIDTH - MARGIN, self.get_y())
        self.ln(3)

        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(100, 100, 100)
        self.cell(80, 4, "Solucion de Programa Lineal")
        fecha = datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 4, f"Fecha: {fecha} | Pagina {self.page_no()}", align=Align.R)