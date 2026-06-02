"""
Modulo de analisis para multiples problemas de programacion lineal.
Genera reportes academicos profesionales usando fpdf2.

Este modulo produce informes detallados para multiples problemas de
programacion lineal, incluyendo analisis de holguras, costos reducidos,
precios sombra y graficos de region factible para problemas de 2 variables.
"""

from __future__ import annotations

import os
import platform
import sys
import tempfile
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import Align, YPos

from ..solver import MultiSolverResult, ProblemResult

# ============================================================
# CONSTANTES DE ESTILO
# ============================================================

# Configuracion de pagina carta
PAGE_WIDTH = 215.9  # mm (carta)
PAGE_HEIGHT = 279.4  # mm
MARGIN = 20  # mm

# Colores
COLOR_PRIMARY = (0, 51, 102)      # Azul oscuro
COLOR_SECONDARY = (100, 100, 100)  # Gris
COLOR_TEXT = (0, 0, 0)             # Negro
COLOR_SUCCESS = (0, 128, 0)         # Verde
COLOR_ERROR = (200, 0, 0)           # Rojo
COLOR_WARNING = (200, 128, 0)       # Naranja
COLOR_BG_HEADER = (0, 51, 102)      # Azul para headers
COLOR_BG_LIGHT = (245, 250, 255)    # Fondo azul claro


# ============================================================
# CLASE BASE DEL REPORTE
# ============================================================

class ReporteAcademicoMulti(FPDF):
    """Clase base para reportes multi-problema."""

    def header(self):
        """No mostrar header en todas las paginas."""
        pass

    def footer(self):
        """Pie de pagina completo."""
        self.set_y(-15)

        # Linea separadora
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_WIDTH - MARGIN, self.get_y())

        self.ln(3)

        # Texto del pie
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)

        # Nombre del reporte - use solver name from MultiLPAnalysis
        solver_name = getattr(self, '_solver_name', 'Multi-Solver')
        self.cell(0, 5, f"Solucion de Programas Lineales - {solver_name}",
                  align=Align.C, new_y=YPos.NEXT)

        # Numero de pagina
        self.cell(0, 5, f"Pagina {self.page_no()}", align=Align.C)



class MultiLPAnalysis:
    """
    Genera reportes academicos profesionales para multiples problemas
    de programacion lineal.
    """

    def __init__(self, results: MultiSolverResult):
        self.results = results
        self.page_count = 0

    def generate_pdf(self, output_path: str) -> None:
        """
        Genera un reporte academico completo para multiples problemas.
        
        Args:
            output_path: Ruta donde se guardara el PDF.
        """
        pdf = ReporteAcademicoMulti()
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(auto=True, margin=15)

        # Store solver_name in PDF object for footer/header
        pdf._solver_name = getattr(self.results, 'solver_name', 'Multi-Solver')

        # Portada
        pdf.add_page()
        self.page_count += 1
        self._build_portada(pdf)

        # Resumen ejecutivo
        pdf.add_page()
        self.page_count += 1
        self._build_resumen(pdf)

        # Pagina para cada problema
        for i, result in enumerate(self.results.results):
            self._build_problema_individual(pdf, result, i + 1)

        # Pagina de resumen de tiempos
        pdf.add_page()
        self.page_count += 1
        self._build_tiempos_resumen(pdf)

        pdf.output(output_path)

    def _build_portada(self, pdf: ReporteAcademicoMulti) -> None:
        """Construye la portada del reporte."""
        # Titulo principal
        pdf.set_font('Helvetica', 'B', 28)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.ln(45)
        pdf.cell(0, 14, "SOLUCION DE PROGRAMAS LINEALES",
                 align=Align.C, new_y=YPos.NEXT)

        pdf.ln(8)

        # Subtitulo
        pdf.set_font('Helvetica', 'I', 16)
        pdf.set_text_color(*COLOR_SECONDARY)
        pdf.cell(0, 12, "Reporte Multi-Problema de Optimizacion",
                 align=Align.C, new_y=YPos.NEXT)

        pdf.ln(35)

        # Informacion del sistema
        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(60, 60, 60)

        num_problems = len(self.results.results)
        exitosos = len(self.results.get_successful_results())
        fallidos = len(self.results.get_failed_results())

        pdf.cell(0, 9, f"Total de problemas: {num_problems}", align=Align.C,
                 new_y=YPos.NEXT)
        pdf.ln(6)
        pdf.cell(0, 9, f"Problemas resueltos: {exitosos}", align=Align.C,
                 new_y=YPos.NEXT)
        pdf.ln(6)
        pdf.cell(0, 9, f"Problemas fallidos: {fallidos}", align=Align.C,
                 new_y=YPos.NEXT)

        pdf.ln(35)

        # Informacion de version
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(100, 100, 100)

        # Get solver name from results
        solver_name = "Multi-Solver"
        if self.results.results:
            # Try to get solver name from the first result's problem or solution
            first_result = self.results.results[0]
            if hasattr(first_result, 'solver_name'):
                solver_name = first_result.solver_name
            elif hasattr(first_result.problem, 'solver_name'):
                solver_name = first_result.problem.solver_name

        pdf.cell(0, 7, f"Optimizador: {solver_name}", align=Align.C,
                 new_y=YPos.NEXT)
        pdf.ln(4)
        pdf.cell(0, 7, f"Python: {sys.version.split()[0]}", align=Align.C,
                 new_y=YPos.NEXT)
        pdf.ln(4)
        pdf.cell(0, 7, f"Plataforma: {platform.system()} {platform.release()}", align=Align.C,
                 new_y=YPos.NEXT)
        pdf.ln(4)
        pdf.cell(0, 7, f"Python: {sys.version.split()[0]}", align=Align.C,
                 new_y=YPos.NEXT)
        pdf.ln(4)
        pdf.cell(0, 7, f"Plataforma: {platform.system()} {platform.release()}",
                 align=Align.C, new_y=YPos.NEXT)

        pdf.ln(30)

        # Fecha detallada
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(100, 100, 100)
        fecha = datetime.now().strftime("%d de %B de %Y a las %H:%M:%S")
        pdf.cell(0, 8, f"Fecha de generacion: {fecha}", align=Align.C,
                 new_y=YPos.NEXT)

        pdf.ln(15)

        # Linea decorativa
        pdf.set_draw_color(*COLOR_PRIMARY)
        pdf.set_line_width(1)
        pdf.line(PAGE_WIDTH/2 - 50, pdf.get_y(),
                 PAGE_WIDTH/2 + 50, pdf.get_y())

        pdf.set_text_color(0, 0, 0)

    def _build_resumen(self, pdf: ReporteAcademicoMulti) -> None:
        """Construye el resumen ejecutivo completo."""
        # Titulo
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 10, "RESUMEN EJECUTIVO", align=Align.C, new_y=YPos.NEXT)

        pdf.ln(5)

        # Linea
        pdf.set_draw_color(*COLOR_PRIMARY)
        pdf.set_line_width(0.8)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(8)

        # Estadisticas
        self._build_estadisticas_resumen(pdf)

        pdf.ln(10)

        # Tabla de resultados
        self._build_tabla_resultados(pdf)

        pdf.ln(10)

        # Interpretacion
        self._build_interpretacion(pdf)

    def _build_estadisticas_resumen(self, pdf: ReporteAcademicoMulti) -> None:
        """Construye las estadisticas del resumen."""
        total = len(self.results.results)
        exitosos = len(self.results.get_successful_results())

        optimos = sum(1 for r in self.results.results
                      if r.solution.status == 'OPTIMAL')
        infeasibles = sum(1 for r in self.results.results
                          if r.solution.status == 'INFEASIBLE')
        unbounded = sum(1 for r in self.results.results
                       if r.solution.status == 'UNBOUNDED')

        # Calcular tiempo promedio
        tiempo_promedio = 0
        if exitosos > 0:
            tiempo_promedio = sum(r.total_time for r in
                                  self.results.get_successful_results()) / exitosos

        # Calcular suma de objetivos
        suma_objetivos = sum(r.solution.objective_value
                             for r in self.results.get_successful_results()
                             if r.solution.objective_value is not None)

        # Fondo para estadisticas
        pdf.set_fill_color(*COLOR_BG_LIGHT)
        pdf.rect(MARGIN, pdf.get_y(), 175.9, 35, 'F')

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)

        # Primera fila
        pdf.cell(58.6, 8, f"Total problemas: {total}", align=Align.C)
        pdf.cell(58.6, 8, f"Optimos: {optimos}", align=Align.C)
        pdf.cell(58.6, 8, f"Exito: {exitosos}/{total}", align=Align.C)
        pdf.ln(8)

        # Segunda fila
        pdf.cell(58.6, 8, f"No optimos: {infeasibles + unbounded}", align=Align.C)
        pdf.cell(58.6, 8, f"Infactibles: {infeasibles}", align=Align.C)
        pdf.cell(58.6, 8, f"No acotados: {unbounded}", align=Align.C)
        pdf.ln(8)

        # Tercera fila
        pdf.cell(58.6, 8, f"Tiempo promedio: {tiempo_promedio*1000:.2f} ms",
                 align=Align.C)
        pdf.cell(117.3, 8, f"Suma de objetivos: {suma_objetivos:,.2f}",
                 align=Align.C)

        pdf.ln(5)

    def _build_tabla_resultados(self, pdf: ReporteAcademicoMulti) -> None:
        """Construye la tabla de resultados."""
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 8, "Resultados por Problema:", new_y=YPos.NEXT)

        pdf.ln(3)

        # Encabezado
        pdf.set_fill_color(*COLOR_BG_HEADER)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(255, 255, 255)

        w = [20, 55, 35, 35.9, 30]
        headers = ["#", "Problema", "Estado", "Valor Optimo", "Tiempo"]

        for i, h in enumerate(headers):
            pdf.cell(w[i], 8, h, align=Align.C, fill=True)
        pdf.ln(8)

        # Datos
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)

        for i, result in enumerate(self.results.results):
            # Determinar color segun estado
            if result.error:
                pdf.set_text_color(*COLOR_ERROR)
                estado = "ERROR"
                valor = (result.error[:15] + "..." if len(result.error) > 15
                         else result.error)
            elif result.solution.status == 'OPTIMAL':
                pdf.set_text_color(*COLOR_SUCCESS)
                estado = "OPTIMO"
                valor = (f"{result.solution.objective_value:,.2f}"
                         if result.solution.objective_value else "N/A")
            elif result.solution.status == 'INFEASIBLE':
                pdf.set_text_color(*COLOR_WARNING)
                estado = "INFACTIBLE"
                valor = "N/A"
            elif result.solution.status == 'UNBOUNDED':
                pdf.set_text_color(*COLOR_WARNING)
                estado = "NO ACOTADO"
                valor = "N/A"
            else:
                pdf.set_text_color(*COLOR_ERROR)
                estado = result.solution.status
                valor = "N/A"

            # Formatear tiempo
            if result.total_time < 1:
                tiempo = f"{result.total_time*1000:.1f} ms"
            else:
                tiempo = f"{result.total_time:.3f} s"

            pdf.cell(w[0], 7, str(i + 1), align=Align.C)
            pdf.cell(w[1], 7, result.problem.name or f"Problema {i + 1}",
                     align=Align.L)
            pdf.cell(w[2], 7, estado, align=Align.C)
            pdf.cell(w[3], 7, valor, align=Align.R)
            pdf.cell(w[4], 7, tiempo, align=Align.R)
            pdf.ln(7)

            pdf.set_text_color(0, 0, 0)

    def _build_interpretacion(self, pdf: ReporteAcademicoMulti) -> None:
        """Construye la interpretacion de resultados."""
        total = len(self.results.results)
        exitosos = len(self.results.get_successful_results())

        porcentaje = (exitosos / total * 100) if total > 0 else 0

        # Fondo
        pdf.set_fill_color(240, 248, 240)
        pdf.rect(MARGIN, pdf.get_y(), 175.9, 15, 'F')

        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(0, 8, f"Interpretacion: {porcentaje:.0f}% de los problemas "
                              f"fueron resueltos de manera optima.",
                 align=Align.C, new_y=YPos.NEXT)

        pdf.set_text_color(0, 0, 0)

    def _build_problema_individual(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult, num: int
    ) -> None:
        """Construye una pagina para un problema individual."""
        # Verificar si necesitamos nueva pagina
        if pdf.get_y() > PAGE_HEIGHT - 80:
            pdf.add_page()
            self.page_count += 1

        pdf.add_page()
        self.page_count += 1

        # Titulo
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 10, f"{result.problem.name or f'Problema {num}'}",
                 align=Align.C, new_y=YPos.NEXT)

        pdf.ln(3)

        # Linea
        pdf.set_draw_color(*COLOR_PRIMARY)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(5)

        # Verificar si hay error
        if result.error:
            self._build_error_problema(pdf, result)
            return

        # Funcion objetivo
        self._build_funcion_objetivo(pdf, result)

        pdf.ln(5)

        # Restricciones
        self._build_restricciones(pdf, result)

        pdf.ln(5)

        # Solucion optima
        self._build_solucion(pdf, result)

        # Analisis de sensibilidad
        self._build_sensibilidad(pdf, result)

        # Grafico si tiene 2 variables
        if len(result.problem.variables) == 2:
            self._build_grafico(pdf, result)

        # Analisis de holguras
        self._build_holguras(pdf, result)

        # Tiempos del problema
        self._build_tiempos_problema(pdf, result)

    def _build_error_problema(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult
    ) -> None:
        """Construye la seccion de error."""
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(*COLOR_ERROR)
        pdf.cell(0, 10, "ERROR EN EL PROBLEMA", align=Align.C, new_y=YPos.NEXT)

        pdf.ln(8)

        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(175.9, 6, f"Mensaje de error: {result.error}")

    def _build_funcion_objetivo(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult
    ) -> None:
        """Construye la seccion de funcion objetivo."""
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, "Funcion Objetivo:", new_y=YPos.NEXT)

        tipo = ("MAXIMIZAR" if result.problem.sense.lower() == "max"
                else "MINIMIZAR")
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(20, 7, f"Tipo: {tipo}")
        pdf.ln()

        # Mostrar funcion objetivo formateada
        obj_str = self._format_objective(result.problem.objective)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(0, 102, 0)
        pdf.cell(15, 8, "Z =")
        pdf.cell(0, 8, obj_str, new_y=YPos.NEXT)

        pdf.set_text_color(0, 0, 0)

    def _build_restricciones(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult
    ) -> None:
        """Construye la tabla de restricciones."""
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, "Restricciones:", new_y=YPos.NEXT)

        pdf.ln(3)

        # Encabezado
        pdf.set_fill_color(*COLOR_BG_HEADER)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)

        w = [12, 90, 20, 25, 28.9]
        headers = ["#", "Expresion", "Tipo", "RHS", "Holgura"]

        for i, h in enumerate(headers):
            pdf.cell(w[i], 7, h, align=Align.C, fill=True)
        pdf.ln(7)

        # Calcular holguras
        holguras = self._calcular_holguras(result)

        # Datos
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)

        for i, c in enumerate(result.problem.constraints):
            cstr = self._format_constraint(c)
            slack = holguras.get(i, 0)

            # Color segun si es activa
            if abs(slack) < 1e-6:
                pdf.set_text_color(*COLOR_ERROR)  # Activa
            else:
                pdf.set_text_color(0, 100, 0)  # No activa

            pdf.cell(w[0], 6, str(i + 1), align=Align.C)
            pdf.cell(w[1], 6, cstr[:40], align=Align.C)
            pdf.cell(w[2], 6, c.sense, align=Align.C)
            pdf.cell(w[3], 6, f"{c.rhs:.2f}", align=Align.C)
            pdf.cell(w[4], 6, f"{slack:.4f}", align=Align.R)
            pdf.ln(6)

            pdf.set_text_color(0, 0, 0)

    def _build_solucion(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult
    ) -> None:
        """Construye la seccion de solucion."""
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 10, "SOLUCION OPTIMA", new_y=YPos.NEXT)

        pdf.ln(3)

        # Estado
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(40, 8, "Estado: ", align=Align.L)

        if result.solution.status == 'OPTIMAL':
            pdf.set_text_color(*COLOR_SUCCESS)
            pdf.cell(0, 8, "OPTIMA", new_y=YPos.NEXT)
        else:
            pdf.set_text_color(*COLOR_ERROR)
            pdf.cell(0, 8, result.solution.status, new_y=YPos.NEXT)

        pdf.ln(3)

        # Valor optimo
        if result.solution.objective_value is not None:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(0, 0, 150)
            pdf.cell(40, 12, "Valor optimo:")
            pdf.cell(0, 12, f"Z* = {result.solution.objective_value:,.4f}",
                     new_y=YPos.NEXT)

        pdf.ln(5)

        # Tabla de valores de variables
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, "Valores de las variables:", new_y=YPos.NEXT)

        pdf.ln(3)

        # Encabezado
        pdf.set_fill_color(*COLOR_BG_HEADER)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(255, 255, 255)

        w = [58, 58.45, 59]
        headers = ["Variable", "Valor Optimo", "Costo Reducido"]

        for i, h in enumerate(headers):
            pdf.cell(w[i], 7, h, align=Align.C, fill=True)
        pdf.ln(7)

        # Datos
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)

        for var, value in result.solution.variables.items():
            pdf.cell(w[0], 6, str(var), align=Align.C)
            pdf.cell(w[1], 6, f"{value:.4f}", align=Align.C)
            pdf.cell(w[2], 6, "0.0000", align=Align.C)
            pdf.ln(6)

    def _build_sensibilidad(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult
    ) -> None:
        """Construye la seccion de analisis de sensibilidad."""
        # Intentar obtener sensibilidad desde la solucion
        sens = getattr(result.solution, 'sensitivity', None)
        if sens is None:
            return

        has_data = (getattr(sens, 'objective_ranges', None) or
                    getattr(sens, 'rhs_ranges', None) or
                    getattr(sens, 'bound_ranges', None))
        if not has_data:
            return

        # Verificar espacio
        if pdf.get_y() > PAGE_HEIGHT - 60:
            pdf.add_page()
            self.page_count += 1

        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 8, "Analisis de Sensibilidad:", new_y=YPos.NEXT)
        pdf.ln(3)

        obj_ranges = getattr(sens, 'objective_ranges', None) or []
        rhs_ranges = getattr(sens, 'rhs_ranges', None) or []

        if obj_ranges:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.cell(0, 6, "Rangos de Coeficientes Objetivo", new_y=YPos.NEXT)
            pdf.ln(2)

            w = [55, 40, 40, 40]
            pdf.set_fill_color(*COLOR_BG_HEADER)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(255, 255, 255)
            for i, h in enumerate(["Variable", "Actual", "Minimo", "Maximo"]):
                pdf.cell(w[i], 6, h, align=Align.C, fill=True)
            pdf.ln(6)

            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(0, 0, 0)
            for r in obj_ranges:
                lower_str = f"{r.lower:.4f}" if r.lower is not None else "-∞"
                upper_str = f"{r.upper:.4f}" if r.upper is not None else "+∞"
                pdf.cell(w[0], 5, str(r.name)[:18], align=Align.C)
                pdf.cell(w[1], 5, f"{r.current:.4f}", align=Align.C)
                pdf.cell(w[2], 5, lower_str, align=Align.C)
                pdf.cell(w[3], 5, upper_str, align=Align.C)
                pdf.ln(5)

        if rhs_ranges:
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.cell(0, 6, "Rangos de Lados Derechos (RHS)", new_y=YPos.NEXT)
            pdf.ln(2)

            w = [55, 40, 40, 40]
            pdf.set_fill_color(*COLOR_BG_HEADER)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_text_color(255, 255, 255)
            for i, h in enumerate(["Restriccion", "Actual", "Minimo", "Maximo"]):
                pdf.cell(w[i], 6, h, align=Align.C, fill=True)
            pdf.ln(6)

            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(0, 0, 0)
            for r in rhs_ranges:
                lower_str = f"{r.lower:.4f}" if r.lower is not None else "-∞"
                upper_str = f"{r.upper:.4f}" if r.upper is not None else "+∞"
                pdf.cell(w[0], 5, str(r.name)[:18], align=Align.C)
                pdf.cell(w[1], 5, f"{r.current:.4f}", align=Align.C)
                pdf.cell(w[2], 5, lower_str, align=Align.C)
                pdf.cell(w[3], 5, upper_str, align=Align.C)
                pdf.ln(5)

    def _build_grafico(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult
    ) -> None:
        """Construye el grafico de region factible usando LinearVisualization."""
        try:
            # Importar la clase de visualizacion existente
            from ..visualization import LinearVisualization

            # Crear visualizador
            viz = LinearVisualization(result.problem, result.solution)

            # Guardar imagen temporal
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_path = tmp.name

            # Generar el grafico
            viz.plot(save_path=temp_path, show=False)

            # Insertar imagen en PDF
            pdf.ln(5)
            pdf.image(temp_path, x=MARGIN, w=175.9)

            # Eliminar archivo temporal
            os.remove(temp_path)

        except ImportError:
            pdf.ln(5)
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(*COLOR_WARNING)
            pdf.cell(0, 6, "Nota: matplotlib no esta instalado. "
                          "No se puede generar el grafico.",
                     align=Align.C, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)

        except Exception as e:
            pdf.ln(5)
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(*COLOR_WARNING)
            pdf.cell(0, 6, f"Nota: No se pudo generar el grafico: {str(e)[:50]}",
                     align=Align.C, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)

    def _build_holguras(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult
    ) -> None:
        """Construye la tabla de analisis de holguras."""
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, "Analisis de Holguras:", new_y=YPos.NEXT)

        pdf.ln(3)

        holguras = self._calcular_holguras(result)

        # Encabezado
        pdf.set_fill_color(*COLOR_BG_HEADER)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(255, 255, 255)

        w = [15, 80, 40, 40.9]
        headers = ["#", "Restriccion", "Holgura", "Estado"]

        for i, h in enumerate(headers):
            pdf.cell(w[i], 7, h, align=Align.C, fill=True)
        pdf.ln(7)

        # Datos
        pdf.set_font('Helvetica', '', 9)

        for i, c in enumerate(result.problem.constraints):
            cstr = self._format_constraint(c)
            slack = holguras.get(i, 0)

            # Determinar estado
            if abs(slack) < 1e-6:
                estado = "ACTIVA (Binding)"
                pdf.set_text_color(*COLOR_ERROR)
            else:
                estado = "NO ACTIVA"
                pdf.set_text_color(0, 100, 0)

            pdf.cell(w[0], 6, str(i + 1), align=Align.C)
            pdf.cell(w[1], 6, cstr[:35], align=Align.C)
            pdf.cell(w[2], 6, f"{slack:.4f}", align=Align.C)
            pdf.cell(w[3], 6, estado, align=Align.C)
            pdf.ln(6)

            pdf.set_text_color(0, 0, 0)

    def _calcular_holguras(self, result: ProblemResult) -> dict:
        """Calcula las holguras de las restricciones."""
        holguras = {}

        for i, c in enumerate(result.problem.constraints):
            if result.solution.variables:
                valor = sum(
                    c.coefficients.get(var, 0) *
                    result.solution.variables.get(var, 0)
                    for var in result.problem.variables
                )

                if c.sense == '<=':
                    slack = c.rhs - valor
                elif c.sense == '>=':
                    slack = valor - c.rhs
                else:
                    slack = 0

                holguras[i] = slack

        return holguras

    def _build_tiempos_problema(
        self, pdf: ReporteAcademicoMulti,
        result: ProblemResult
    ) -> None:
        """Construye la seccion de tiempos de un problema."""
        # Verificar espacio
        if pdf.get_y() > PAGE_HEIGHT - 50:
            pdf.add_page()
            self.page_count += 1

        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 8, "Tiempos de Ejecucion:", new_y=YPos.NEXT)

        pdf.set_draw_color(*COLOR_PRIMARY)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(3)

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)

        times_data = [
            ("Construccion del modelo", result.build_time),
            ("Resolucion (Gurobi)", result.solve_time),
            ("Tiempo total", result.total_time),
        ]

        for stage, time_val in times_data:
            tiempo_str = self._format_tiempo(time_val)
            pdf.cell(100, 6, stage)
            pdf.cell(75.9, 6, tiempo_str, align=Align.R)
            pdf.ln(6)

        pdf.ln(3)

    def _format_tiempo(self, seconds: float) -> str:
        """Formatea el tiempo de manera consistente."""
        if seconds < 1:
            return f"{seconds*1000:.2f} ms"
        else:
            return f"{seconds:.3f} s"

    def _build_tiempos_resumen(self, pdf: ReporteAcademicoMulti) -> None:
        """Construye el resumen de tiempos."""
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 10, "ANALISIS DE TIEMPOS", align=Align.C, new_y=YPos.NEXT)

        pdf.ln(5)

        pdf.set_draw_color(*COLOR_PRIMARY)
        pdf.set_line_width(0.8)
        pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
        pdf.ln(8)

        # Informacion tecnica
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)

        pdf.cell(90, 5, f"Python: {sys.version.split()[0]}")
        pdf.cell(90, 5, f"Sistema: {platform.system()}", new_y=YPos.NEXT)
        pdf.ln(4)

        pdf.cell(90, 5, f"Procesador: {platform.processor()}")
        fecha_gen = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pdf.cell(90, 5, f"Fecha: {fecha_gen}", new_y=YPos.NEXT)
        pdf.ln(10)

        # Tabla de tiempos
        pdf.set_fill_color(*COLOR_BG_HEADER)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(255, 255, 255)

        pdf.cell(87.95, 8, "Etapa", align=Align.C, fill=True)
        pdf.cell(87.95, 8, "Tiempo", align=Align.C, fill=True)
        pdf.ln(8)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)

        times_data = [
            ("Parseo de problemas", self.results.total_parse_time),
            ("Construccion de modelos", self.results.total_build_time),
            ("Resolucion (Gurobi)", self.results.total_solve_time),
        ]

        for stage, time_val in times_data:
            pdf.cell(87.95, 7, stage, align=Align.L)
            pdf.cell(87.95, 7, self._format_tiempo(time_val), align=Align.R)
            pdf.ln(7)

        # Total
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_draw_color(*COLOR_PRIMARY)
        pdf.set_line_width(0.5)
        pdf.line(MARGIN + 5, pdf.get_y(), PAGE_WIDTH - MARGIN - 5,
                 pdf.get_y())
        pdf.ln(2)

        pdf.cell(87.95, 7, "TIEMPO TOTAL", align=Align.L)
        pdf.cell(87.95, 7, self._format_tiempo(self.results.total_time),
                 align=Align.R)

        pdf.ln(15)

        # Tabla por problema con estado
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 8, "Tiempos por Problema:", new_y=YPos.NEXT)

        pdf.ln(3)

        pdf.set_fill_color(*COLOR_BG_HEADER)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)

        w = [20, 40, 35, 40, 40.9]
        headers = ["#", "Problema", "Estado", "Build", "Solve"]

        for i, h in enumerate(headers):
            pdf.cell(w[i], 7, h, align=Align.C, fill=True)
        pdf.ln(7)

        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)

        for i, result in enumerate(self.results.results):
            # Color segun estado
            if result.error:
                pdf.set_text_color(*COLOR_ERROR)
                estado = "ERROR"
            elif result.solution.status == 'OPTIMAL':
                pdf.set_text_color(*COLOR_SUCCESS)
                estado = "OPTIMO"
            else:
                pdf.set_text_color(*COLOR_WARNING)
                estado = result.solution.status[:8]

            pdf.cell(w[0], 6, str(i + 1), align=Align.C)
            pdf.cell(w[1], 6, f"P{i+1}", align=Align.C)
            pdf.cell(w[2], 6, estado, align=Align.C)
            pdf.cell(w[3], 6, f"{result.build_time*1000:.1f} ms", align=Align.C)
            pdf.cell(w[4], 6, f"{result.solve_time*1000:.1f} ms", align=Align.C)
            pdf.ln(6)

            pdf.set_text_color(0, 0, 0)

    def _format_objective(self, obj: dict) -> str:
        """Formatea la funcion objetivo."""
        terms = []
        for var in sorted(obj.keys()):
            coeff = obj[var]
            if coeff == 0:
                continue
            if coeff >= 0:
                terms.append(f"+{coeff}{var}" if coeff != 1 else f"+{var}")
            else:
                terms.append(f"{coeff}{var}" if coeff != -1 else f"-{var}")

        if not terms:
            return "0"

        result = " ".join(terms)
        if result.startswith("+"):
            result = result[1:]
        return result

    def _format_constraint(self, c) -> str:
        """Formatea una restriccion."""
        terms = []
        for var in sorted(c.coefficients.keys()):
            coeff = c.coefficients[var]
            if coeff == 0:
                continue
            if coeff >= 0:
                terms.append(f"+{coeff}{var}" if coeff != 1 else f"+{var}")
            else:
                terms.append(f"{coeff}{var}" if coeff != -1 else f"-{var}")

        if not terms:
            return "0"

        result = " ".join(terms)
        if result.startswith("+"):
            result = result[1:]
        return result
