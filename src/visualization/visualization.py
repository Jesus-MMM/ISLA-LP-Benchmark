"""
Modulo de visualizacion para problemas de programacion lineal.
"""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TABLEAU_COLORS as TAB10_COLORS
from matplotlib.patches import Polygon

from ..core import LinearConstraint, LinearProblem, Solution


class LinearVisualization:
    """Visualiza problemas de programacion lineal en 2D."""

    def __init__(self, problem: LinearProblem, solution: Solution | None = None):
        if len(problem.variables) != 2:
            raise ValueError(
                f"La visualizacion solo funciona con 2 variables. "
                f"El problema tiene {len(problem.variables)} variables."
            )

        self.problem = problem
        self.solution = solution
        self.var_x = problem.variables[0]
        self.var_y = problem.variables[1]
        self.colors = list(TAB10_COLORS)

    def find_intersection(self, c1: LinearConstraint, c2: LinearConstraint) -> tuple[float, float] | None:
        a1 = c1.coefficients.get(self.var_x, 0)
        b1 = c1.coefficients.get(self.var_y, 0)
        r1 = c1.rhs

        a2 = c2.coefficients.get(self.var_x, 0)
        b2 = c2.coefficients.get(self.var_y, 0)
        r2 = c2.rhs

        det = a1 * b2 - a2 * b1

        if abs(det) < 1e-10:
            return None

        x = (r1 * b2 - r2 * b1) / det
        y = (a1 * r2 - a2 * r1) / det

        return (x, y)

    def is_point_feasible(self, x: float, y: float, constraints: list[LinearConstraint]) -> bool:
        for c in constraints:
            value = c.coefficients.get(self.var_x, 0) * x + c.coefficients.get(self.var_y, 0) * y

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

    def _get_all_constraints(self) -> list[LinearConstraint]:
        """Obtiene todas las restricciones incluyendo bounds como restricciones."""
        constraints = list(self.problem.constraints)
        bounds = self.problem.bounds

        x_bound = bounds.get(self.var_x)
        y_bound = bounds.get(self.var_y)

        if x_bound is None:
            constraints.append(LinearConstraint(coefficients={self.var_x: 1}, rhs=0, sense=">="))
        else:
            if x_bound.lower is not None:
                constraints.append(LinearConstraint(coefficients={self.var_x: 1}, rhs=x_bound.lower, sense=">="))
            if x_bound.upper is not None:
                constraints.append(LinearConstraint(coefficients={self.var_x: 1}, rhs=x_bound.upper, sense="<="))

        if y_bound is None:
            constraints.append(LinearConstraint(coefficients={self.var_y: 1}, rhs=0, sense=">="))
        else:
            if y_bound.lower is not None:
                constraints.append(LinearConstraint(coefficients={self.var_y: 1}, rhs=y_bound.lower, sense=">="))
            if y_bound.upper is not None:
                constraints.append(LinearConstraint(coefficients={self.var_y: 1}, rhs=y_bound.upper, sense="<="))

        return constraints

    def _calculate_plot_range(self) -> tuple[float, float, float, float]:
        """Calcula el rango de la grafica para mostrar los 4 cuadrantes."""
        x_min, x_max = -20, 50
        y_min, y_max = -20, 50

        all_constraints = self._get_all_constraints()

        for c in all_constraints:
            a = c.coefficients.get(self.var_x, 0)
            b = c.coefficients.get(self.var_y, 0)
            rhs = c.rhs

            if abs(b) < 1e-10 and abs(a) > 1e-10:
                val = rhs / a
                x_max = max(x_max, abs(val) * 1.5)
                x_min = min(x_min, -abs(val) * 0.5)
            elif abs(a) < 1e-10 and abs(b) > 1e-10:
                val = rhs / b
                y_max = max(y_max, abs(val) * 1.5)
                y_min = min(y_min, -abs(val) * 0.5)
            else:
                if abs(b) > 1e-10:
                    x_intercept = rhs / b
                    x_max = max(x_max, abs(x_intercept) * 1.5)
                    x_min = min(x_min, -abs(x_intercept) * 0.5)
                if abs(a) > 1e-10:
                    y_intercept = rhs / a
                    y_max = max(y_max, abs(y_intercept) * 1.5)
                    y_min = min(y_min, -abs(y_intercept) * 0.5)

        if self.solution and self.solution.variables:
            sol_x = self.solution.variables.get(self.var_x, 0)
            sol_y = self.solution.variables.get(self.var_y, 0)

            x_max = max(x_max, abs(sol_x) + 5)
            y_max = max(y_max, abs(sol_y) + 5)
            x_min = min(x_min, -abs(sol_x) * 0.3 - 2) if sol_x > 0 else min(x_min, sol_x - 2)
            y_min = min(y_min, -abs(sol_y) * 0.3 - 2) if sol_y > 0 else min(y_min, sol_y - 2)

        x_range = x_max - x_min
        if x_range < 15:
            center = (x_max + x_min) / 2
            x_min = center - 7.5
            x_max = center + 7.5

        y_range = y_max - y_min
        if y_range < 15:
            center = (y_max + y_min) / 2
            y_min = center - 7.5
            y_max = center + 7.5

        return x_min, x_max, y_min, y_max

    def _find_feasible_vertices(self, constraints: list[LinearConstraint]) -> list[tuple[float, float]]:
        """Encuentra todos los vertices de la region factible."""
        vertices = []

        for i, c1 in enumerate(constraints):
            for c2 in constraints[i+1:]:
                intersection = self.find_intersection(c1, c2)
                if intersection:
                    x, y = intersection
                    if self.is_point_feasible(x, y, constraints):
                        if not any(math.isclose(x, v[0], abs_tol=1e-8) and
                                  math.isclose(y, v[1], abs_tol=1e-8) for v in vertices):
                            vertices.append((x, y))

        bounds = self.problem.bounds

        x_bound = bounds.get(self.var_x)
        y_bound = bounds.get(self.var_y)

        x_lower = x_bound.lower if x_bound and x_bound.lower is not None else 0
        y_lower = y_bound.lower if y_bound and y_bound.lower is not None else 0

        corner_points = [
            (x_lower, y_lower),
        ]

        for px, py in corner_points:
            if self.is_point_feasible(px, py, constraints):
                if not any(math.isclose(px, v[0], abs_tol=1e-8) and
                          math.isclose(py, v[1], abs_tol=1e-8) for v in vertices):
                    vertices.append((px, py))

        return vertices

    def _order_vertices_ccw(self, vertices: list[tuple[float, float]]) -> list[tuple[float, float]]:
        """Ordena vertices en sentido antihorario."""
        if len(vertices) < 3:
            return vertices

        cx = sum(v[0] for v in vertices) / len(vertices)
        cy = sum(v[1] for v in vertices) / len(vertices)

        vertices_sorted = sorted(vertices, key=lambda v: math.atan2(v[1] - cy, v[0] - cx))

        return vertices_sorted

    def _get_line_points(self, c: LinearConstraint, x_min: float, x_max: float,
                        y_min: float, y_max: float) -> tuple[np.ndarray, np.ndarray]:
        """Obtiene puntos para graficar una restriccion."""
        a = c.coefficients.get(self.var_x, 0)
        b = c.coefficients.get(self.var_y, 0)
        rhs = c.rhs

        if abs(b) < 1e-10 and abs(a) > 1e-10:
            x_const = rhs / a
            y_vals = np.linspace(y_min, y_max, 100)
            x_line = np.full_like(y_vals, x_const)
            return x_line, y_vals
        elif abs(a) < 1e-10 and abs(b) > 1e-10:
            y_const = rhs / b
            x_vals = np.linspace(x_min, x_max, 100)
            y_line = np.full_like(x_vals, y_const)
            return x_vals, y_line
        else:
            x_vals = np.linspace(x_min, x_max, 200)
            y_vals = (rhs - a * x_vals) / b

            valid = np.isfinite(y_vals) & (y_vals >= y_min - 10) & (y_vals <= y_max + 10)

            return x_vals[valid], y_vals[valid]

    def plot(self, save_path: str | None = None, show: bool = True) -> None:
        """Genera la visualizacion completa del problema."""
        x_min, x_max, y_min, y_max = self._calculate_plot_range()

        fig, ax = plt.subplots(figsize=(10, 8))

        all_constraints = self._get_all_constraints()

        for i, c in enumerate(self.problem.constraints):
            x_vals, y_vals = self._get_line_points(c, x_min, x_max, y_min, y_max)

            linestyle = '-' if c.sense == "<=" else ('--' if c.sense == ">=" else ':')
            color = self.colors[i % len(self.colors)]

            ax.plot(x_vals, y_vals, linestyle=linestyle, color=color,
                   linewidth=2.5, label=f'R{i+1}')

        vertices = self._find_feasible_vertices(all_constraints)
        vertices = self._order_vertices_ccw(vertices)

        if len(vertices) >= 3:
            polygon = Polygon(vertices, closed=True, alpha=0.35,
                             facecolor='#90EE90', edgecolor='#228B22', linewidth=2)
            ax.add_patch(polygon)
        elif len(vertices) == 2:
            cx = (vertices[0][0] + vertices[1][0]) / 2
            cy = (vertices[0][1] + vertices[1][1]) / 2
            if abs(cx - x_min) < abs(cx - x_max) and abs(cx - x_min) < (x_max - x_min) * 0.1:
                ex, ey = x_min, cy
            elif abs(cx - x_max) < abs(cx - x_min) and abs(cx - x_max) < (x_max - x_min) * 0.1:
                ex, ey = x_max, cy
            elif abs(cy - y_min) < abs(cy - y_max) and abs(cy - y_min) < (y_max - y_min) * 0.1:
                ex, ey = cx, y_min
            else:
                ex, ey = cx, y_max

            polygon = Polygon([vertices[0], vertices[1], (ex, ey)], closed=True, alpha=0.35,
                             facecolor='#90EE90', edgecolor='#228B22', linewidth=2)
            ax.add_patch(polygon)
        elif len(vertices) == 1:
            ax.scatter([vertices[0][0]], [vertices[0][1]], color='#90EE90', s=500, zorder=3,
                      marker='s', alpha=0.5)

        for i, c in enumerate(all_constraints):
            if c not in self.problem.constraints:
                x_vals, y_vals = self._get_line_points(c, x_min, x_max, y_min, y_max)
                linestyle = '-' if c.sense == "<=" else ('--' if c.sense == ">=" else ':')
                ax.plot(x_vals, y_vals, linestyle=linestyle, color='gray',
                       linewidth=1.5, alpha=0.6, label='Bound')

        intersections = []
        for i, c1 in enumerate(all_constraints):
            for c2 in all_constraints[i+1:]:
                intersection = self.find_intersection(c1, c2)
                if intersection and self.is_point_feasible(intersection[0], intersection[1], all_constraints):
                    intersections.append(intersection)

        if intersections:
            ax.scatter([p[0] for p in intersections], [p[1] for p in intersections],
                      color='red', s=80, zorder=5, edgecolors='black', linewidths=1)

            for idx, (x, y) in enumerate(intersections):
                ax.annotate(f'P{idx+1}', (x, y), textcoords="offset points",
                           xytext=(8, 8), fontsize=9, fontweight='bold', color='red')

        if self.solution and self.solution.variables:
            x = self.solution.variables.get(self.var_x, 0)
            y = self.solution.variables.get(self.var_y, 0)

            ax.scatter([x], [y], color='gold', s=400, zorder=10, marker='*',
                      edgecolors='black', linewidths=2)

            ax.annotate(f'Optimo\n({x:.2f}, {y:.2f})', (x, y),
                       textcoords="offset points", xytext=(15, 15),
                       fontsize=11, fontweight='bold', color='darkred',
                       arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5),
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

            obj = self.problem.objective
            a = obj.get(self.var_x, 0)
            b = obj.get(self.var_y, 0)

            if abs(a) > 1e-10 or abs(b) > 1e-10:
                opt_value = a * x + b * y

                x_line = np.linspace(x_min, x_max, 200)

                if abs(b) > 1e-10:
                    y_obj = (opt_value - a * x_line) / b
                    valid = np.isfinite(y_obj) & (y_obj >= y_min - 5) & (y_obj <= y_max + 5)
                    ax.plot(x_line[valid], y_obj[valid], 'b--', alpha=0.7,
                           linewidth=2, label=f'Funcion objetivo (Z={opt_value:.2f})')
                elif abs(a) > 1e-10:
                    x_const = opt_value / a
                    ax.axvline(x_const, color='b', linestyle='--', alpha=0.7,
                               linewidth=2, label=f'Funcion objetivo (Z={opt_value:.2f})')

        padding_x = (x_max - x_min) * 0.05
        padding_y = (y_max - y_min) * 0.05
        ax.set_xlim(x_min - padding_x, x_max + padding_x)
        ax.set_ylim(y_min - padding_y, y_max + padding_y)

        ax.set_xlabel(self.var_x, fontsize=14, fontweight='bold')
        ax.set_ylabel(self.var_y, fontsize=14, fontweight='bold')

        obj_str = self._format_objective()
        ax.set_title(f'Region Factible - {self.problem.sense.upper()}\nZ = {obj_str}',
                    fontsize=13, fontweight='bold')

        ax.grid(True, alpha=0.3, linestyle='--')
        ax.axhline(y=0, color='black', linewidth=1.2)
        ax.axvline(x=0, color='black', linewidth=1.2)

        ax.legend(loc='upper right', fontsize=9, framealpha=0.95)

        ax.set_facecolor('#f8f8f8')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')

        if show:
            import matplotlib
            if matplotlib.get_backend() != 'Agg':
                plt.show()

        plt.close()

    def plot_to_tempfile(self) -> str:
        """Genera la visualización y la guarda en un archivo temporal. Retorna la ruta."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            self.plot(save_path=tmp.name, show=False)
            return tmp.name


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
