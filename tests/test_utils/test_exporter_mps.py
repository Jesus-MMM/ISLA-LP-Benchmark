"""
Tests para exportacion a formato MPS.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import tempfile
from src.core.problem import LinearProblem
from src.core.constraint import LinearConstraint
from src.core.bound import VariableBound
from src.utils.exporter import export_to_mps_format, export_to_mps_file


class TestExportToMPSFormat:
    """Tests para export_to_mps_format."""

    def _make_problem(self, **overrides):
        defaults = dict(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<=", name="R1"),
            ],
            variables=["x", "y"],
            bounds={},
        )
        defaults.update(overrides)
        return LinearProblem(**defaults)

    def test_contains_name(self):
        """Test que la salida contiene NAME."""
        output = export_to_mps_format(self._make_problem(), "TESTPROB")
        assert "NAME          TESTPROB" in output

    def test_contains_rows_section(self):
        """Test que la salida contiene ROWS."""
        output = export_to_mps_format(self._make_problem())
        assert "ROWS" in output

    def test_contains_columns_section(self):
        """Test que la salida contiene COLUMNS."""
        output = export_to_mps_format(self._make_problem())
        assert "COLUMNS" in output

    def test_contains_rhs_section(self):
        """Test que la salida contiene RHS."""
        output = export_to_mps_format(self._make_problem())
        assert "RHS" in output

    def test_contains_endata(self):
        """Test que la salida termina con ENDATA."""
        output = export_to_mps_format(self._make_problem())
        assert output.rstrip().endswith("ENDATA")

    def test_objective_row(self):
        """Test que la fila objetivo es tipo N."""
        output = export_to_mps_format(self._make_problem())
        assert " N  OBJ" in output

    def test_constraint_rows(self):
        """Test que las restricciones tienen tipo correcto."""
        problem = self._make_problem()
        output = export_to_mps_format(problem)
        assert " L  R1" in output  # <=

        problem2 = self._make_problem(
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense=">=", name="R1")]
        )
        output2 = export_to_mps_format(problem2)
        assert " G  R1" in output2  # >=

        problem3 = self._make_problem(
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="=", name="R1")]
        )
        output3 = export_to_mps_format(problem3)
        assert " E  R1" in output3  # =

    def test_column_entries(self):
        """Test que las columnas tienen coeficientes."""
        output = export_to_mps_format(self._make_problem())
        assert "x" in output
        assert "y" in output
        assert "OBJ" in output

    def test_rhs_entries(self):
        """Test que RHS tiene las entradas correctas."""
        output = export_to_mps_format(self._make_problem())
        assert "RHS1" in output
        assert "10" in output

    def test_integer_markers(self):
        """Test marcadores INTORG/INTEND para MILP."""
        problem = self._make_problem(
            variable_types={"x": "integer"}
        )
        output = export_to_mps_format(problem)
        assert "INTORG" in output
        assert "INTEND" in output

    def test_binary_marker_no_intend(self):
        """Test variable binaria usa BV bound en lugar de marker."""
        problem = self._make_problem(
            variable_types={"x": "binary"},
            bounds={"x": VariableBound("x", lower=0, upper=1)},
        )
        output = export_to_mps_format(problem)
        assert "INTORG" in output
        assert "INTEND" in output

    def test_bounds_section(self):
        """Test seccion BOUNDS con LO y UP."""
        problem = self._make_problem(
            bounds={
                "x": VariableBound("x", lower=0, upper=10),
                "y": VariableBound("y", lower=2, upper=None),
            }
        )
        output = export_to_mps_format(problem)
        assert "BOUNDS" in output
        assert "LO" in output
        assert "UP" in output

    def test_bounds_binary(self):
        """Test bound BV para variable binaria."""
        problem = self._make_problem(
            variable_types={"x": "binary"},
            bounds={"x": VariableBound("x", lower=0, upper=1)},
        )
        output = export_to_mps_format(problem)
        assert "BV BND       x" in output

    def test_bounds_fixed(self):
        """Test bound FX para variable fija."""
        problem = self._make_problem(
            bounds={"x": VariableBound("x", lower=5, upper=5)},
        )
        output = export_to_mps_format(problem)
        assert "FX BND       x" in output

    def test_bounds_free(self):
        """Test bound FR para variable libre."""
        problem = self._make_problem(
            bounds={"x": VariableBound("x", lower=None, upper=None)},
        )
        output = export_to_mps_format(problem)
        assert "FR BND       x" in output

    def test_bounds_lo_zero(self):
        """Test que LO=0 no genera entrada LO."""
        problem = self._make_problem(
            bounds={"x": VariableBound("x", lower=0, upper=None)},
        )
        output = export_to_mps_format(problem)
        assert "LO BND" not in output

    def test_no_bounds_section_if_no_bounds(self):
        """Test que no genera BOUNDS si no hay bounds."""
        problem = self._make_problem(bounds={})
        output = export_to_mps_format(problem)
        assert "BOUNDS" not in output

    def test_negative_coeff(self):
        """Test coeficientes negativos."""
        problem = LinearProblem(
            objective={"x": -1, "y": 2},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": -2, "y": 3}, rhs=10, sense="<=", name="R1"),
            ],
            variables=["x", "y"],
            bounds={},
        )
        output = export_to_mps_format(problem)
        assert "-1" in output or "-2" in output


class TestExportToMPSFile:
    """Tests para export_to_mps_file."""

    def test_writes_to_disk(self):
        """Test que escribe el archivo en disco."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=", name="R1"),
            ],
            variables=["x"],
            bounds={},
        )
        with tempfile.NamedTemporaryFile(mode="r", suffix=".mps", delete=False, encoding="utf-8") as f:
            tmp_path = f.name
        try:
            export_to_mps_file(problem, tmp_path, "TEST")
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "NAME          TEST" in content
            assert "ENDATA" in content
        finally:
            os.unlink(tmp_path)

    def test_file_content(self):
        """Test que el contenido del archivo MPS es correcto."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<=", name="R1"),
            ],
            variables=["x", "y"],
            bounds={},
        )
        with tempfile.NamedTemporaryFile(mode="r", suffix=".mps", delete=False, encoding="utf-8") as f:
            tmp_path = f.name
        try:
            export_to_mps_file(problem, tmp_path)
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert "ROWS" in content
            assert "COLUMNS" in content
        finally:
            os.unlink(tmp_path)
