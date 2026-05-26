"""
Tests para el exportador de problemas LP.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import tempfile
from src.core.problem import LinearProblem
from src.core.constraint import LinearConstraint
from src.core.bound import VariableBound
from src.utils.exporter import export_to_lp_format, export_to_lp_file


class TestExportToLPFormat:
    """Tests para export_to_lp_format."""

    def test_contains_minimize(self):
        """Test que la salida contiene Minimize."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="min",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<="),
            ],
            variables=["x", "y"],
            bounds={},
        )
        output = export_to_lp_format(problem, "test_prob")
        assert "Minimize" in output

    def test_contains_maximize(self):
        """Test que la salida contiene Maximize."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        output = export_to_lp_format(problem)
        assert "Maximize" in output

    def test_contains_subject_to(self):
        """Test que la salida contiene Subject To."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<="),
            ],
            variables=["x"],
            bounds={},
        )
        output = export_to_lp_format(problem)
        assert "Subject To" in output

    def test_contains_bounds_section(self):
        """Test que la salida contiene Bounds."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={"x": VariableBound("x", lower=0, upper=10)},
        )
        output = export_to_lp_format(problem)
        assert "Bounds" in output

    def test_contains_end(self):
        """Test que la salida contiene End."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        output = export_to_lp_format(problem)
        assert output.rstrip().endswith("End")

    def test_problem_name_in_output(self):
        """Test que el nombre del problema aparece en la salida."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        output = export_to_lp_format(problem, "MiProblema")
        assert "MiProblema" in output

    def test_constraints_in_output(self):
        """Test que las restricciones aparecen en la salida."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=", name="c1"),
            ],
            variables=["x"],
            bounds={},
        )
        output = export_to_lp_format(problem)
        assert "c1" in output
        assert "<" in output
        assert "10" in output

    def test_bounds_format(self):
        """Test formato de bounds en la salida."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={"x": VariableBound("x", lower=0, upper=100)},
        )
        output = export_to_lp_format(problem)
        assert "0 <= x <= 100" in output

    def test_no_bounds_default_nonnegativity(self):
        """Test default no-negatividad cuando no hay bounds."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        output = export_to_lp_format(problem)
        assert ">= 0" in output

    def test_expression_with_float_coeffs(self):
        """Test formato de expresion con coeficientes flotantes."""
        problem = LinearProblem(
            objective={"x": 1.5, "y": 2.5},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        output = export_to_lp_format(problem)
        assert "1.5" in output or "1.5" in output
        assert "2.5" in output

    def test_zero_coefficient_omitted(self):
        """Test que coeficiente cero se omite de la expresion."""
        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        output = export_to_lp_format(problem)
        assert "y" not in output.split("objective")[1].split("\n")[0]


class TestExportToLPFile:
    """Tests para export_to_lp_file."""

    def test_writes_to_disk(self):
        """Test que escribe el archivo en disco."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        with tempfile.NamedTemporaryFile(mode="r", suffix=".lp", delete=False, encoding="utf-8") as f:
            tmp_path = f.name
        try:
            export_to_lp_file(problem, tmp_path, "test_file")
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "Maximize" in content
            assert "End" in content
        finally:
            os.unlink(tmp_path)

    def test_file_content_minimize(self):
        """Test que el contenido del archivo es correcto para minimizacion."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="min",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        with tempfile.NamedTemporaryFile(mode="r", suffix=".lp", delete=False, encoding="utf-8") as f:
            tmp_path = f.name
        try:
            export_to_lp_file(problem, tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "Minimize" in content
        finally:
            os.unlink(tmp_path)
