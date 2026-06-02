"""
Tests para el parser de formato MPS.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import tempfile

import pytest

from src.parser.mps_parser import MPSParser


class TestMPSParserBasic:
    """Tests basicos del parser MPS."""

    def test_simple_lp(self):
        """Test problema LP simple en MPS."""
        mps = """NAME          TESTPROB
ROWS
 N  OBJ
 L  R1
 G  R2
 E  R3
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
    X1          R2        -1.0
    X2          OBJ        2.0
    X2          R1         3.0
    X2          R3         1.0
RHS
    RHS1        R1         5.0
    RHS1        R2         3.0
    RHS1        R3         4.0
BOUNDS
 LO BND       X1         0.0
 UP BND       X1        10.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.sense == "max"
        assert "X1" in problem.variables
        assert "X2" in problem.variables
        assert problem.objective["X1"] == 1.0
        assert problem.objective["X2"] == 2.0
        assert len(problem.constraints) == 3

    def test_integer_vars_with_markers(self):
        """Test variables enteras con marcadores INTORG/INTEND."""
        mps = """NAME          MILP
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
    X2          OBJ        3.0
    X2          R1         4.0
    MARKER      'MARKER'                 'INTORG'
    X3          OBJ        5.0
    X3          R1         6.0
    X4          OBJ        7.0
    X4          R1         8.0
    MARKER      'MARKER'                 'INTEND'
RHS
    RHS1        R1        10.0
BOUNDS
 LO BND       X1         0.0
 LO BND       X3         0.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.variable_types["X3"] == "integer"
        assert problem.variable_types["X4"] == "integer"
        assert problem.variable_types["X1"] == "continuous"
        assert problem.variable_types["X2"] == "continuous"

    def test_marker_without_quotes(self):
        """Test marcadores sin comillas."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
    MARKER      MARKER                 'INTORG'
    X2          OBJ        3.0
    X2          R1         4.0
    MARKER      MARKER                 'INTEND'
RHS
    RHS1        R1         5.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert "X2" in problem.variable_types

    def test_empty_objective_error(self):
        """Test error cuando no hay objetivo."""
        mps = """NAME          TEST
ROWS
 L  R1
COLUMNS
    X1          R1         1.0
RHS
    RHS1        R1         5.0
ENDATA"""
        with pytest.raises(ValueError, match="No se encontr"):
        #with pytest.raises(ValueError, match="fila tipo N"):
            MPSParser(mps).parse()

    def test_no_constraints_error(self):
        """Test error cuando no hay restricciones."""
        mps = """NAME          TEST
ROWS
 N  OBJ
COLUMNS
    X1          OBJ        1.0
RHS
    RHS1        OBJ        5.0
ENDATA"""
        with pytest.raises(ValueError, match="al menos una restricci"):
            MPSParser(mps).parse()

    def test_empty_objective_coeffs_error(self):
        """Test error cuando el objetivo no tiene coeficientes."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          R1         1.0
RHS
    RHS1        R1         5.0
ENDATA"""
        with pytest.raises(ValueError, match="vac"):
            MPSParser(mps).parse()

    def test_parse_file(self):
        """Test parse_file."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
RHS
    RHS1        R1         5.0
ENDATA"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mps", delete=False, encoding="utf-8") as f:
            f.write(mps)
            tmp_path = f.name
        try:
            problem = MPSParser("").parse_file(tmp_path)
            assert len(problem.variables) == 1
        finally:
            os.unlink(tmp_path)


class TestMPSParserBoundTypes:
    """Tests para diferentes tipos de bounds MPS."""

    MPS_HEADER = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         1.0
RHS
    RHS1        R1         5.0
"""

    def _parse_with_bounds(self, bound_lines: str):
        mps = self.MPS_HEADER + "BOUNDS\n" + bound_lines + "ENDATA"
        return MPSParser(mps).parse()

    def test_fr_bound(self):
        """Test FR (free)."""
        problem = self._parse_with_bounds(" FR BND       X1\n")
        assert problem.bounds["X1"].lower is None
        assert problem.bounds["X1"].upper is None

    def test_lo_bound(self):
        """Test LO (lower)."""
        problem = self._parse_with_bounds(" LO BND       X1         3.0\n")
        assert problem.bounds["X1"].lower == 3.0

    def test_up_bound(self):
        """Test UP (upper)."""
        problem = self._parse_with_bounds(" UP BND       X1         7.0\n")
        assert problem.bounds["X1"].upper == 7.0

    def test_fx_bound(self):
        """Test FX (fixed)."""
        problem = self._parse_with_bounds(" FX BND       X1         4.0\n")
        assert problem.bounds["X1"].lower == 4.0
        assert problem.bounds["X1"].upper == 4.0

    def test_mi_bound(self):
        """Test MI (minus infinity)."""
        problem = self._parse_with_bounds(" MI BND       X1\n")
        assert problem.bounds["X1"].lower is None

    def test_pl_bound(self):
        """Test PL (plus infinity)."""
        problem = self._parse_with_bounds(" PL BND       X1\n")
        assert problem.bounds["X1"].upper is None

    def test_bv_bound(self):
        """Test BV (binary)."""
        problem = self._parse_with_bounds(" BV BND       X1\n")
        assert problem.bounds["X1"].lower == 0.0
        assert problem.bounds["X1"].upper == 1.0
        assert problem.variable_types["X1"] == "binary"

    def test_li_bound(self):
        """Test LI (lower integer)."""
        problem = self._parse_with_bounds(" LI BND       X1         2.0\n")
        assert problem.variable_types["X1"] == "integer"

    def test_ui_bound(self):
        """Test UI (upper integer)."""
        problem = self._parse_with_bounds(" UI BND       X1         5.0\n")
        assert problem.variable_types["X1"] == "integer"


class TestMPSParserRanges:
    """Tests para la seccion RANGES."""

    def test_range_less_equal(self):
        """Test RANGE con restriccion <=: rhs aumenta."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         1.0
RHS
    RHS1        R1         5.0
RANGES
    RNG1        R1         3.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert len(problem.constraints) == 1
        assert problem.constraints[0].rhs == 8.0  # 5 + 3

    def test_range_greater_equal(self):
        """Test RANGE con restriccion >=: rhs disminuye."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 G  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         1.0
RHS
    RHS1        R1         5.0
RANGES
    RNG1        R1         3.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.constraints[0].rhs == 2.0  # 5 - 3


class TestMPSParserCommentsAndEmpty:
    """Tests para comentarios y lineas vacias."""

    def test_comments(self):
        """Test que ignora lineas de comentario."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
* Esta es una linea de comentario
    X1          R1         2.0
RHS
    RHS1        R1         5.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert len(problem.constraints) == 1

    def test_empty_lines(self):
        """Test que ignora lineas vacias."""
        mps = """NAME          TEST

ROWS
 N  OBJ
 L  R1

COLUMNS
    X1          OBJ        1.0

    X1          R1         2.0
RHS
    RHS1        R1         5.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert len(problem.constraints) == 1

    def test_two_columns_per_line(self):
        """Test dos columnas por linea en COLUMNS."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
 L  R2
COLUMNS
    X1          OBJ        1.0     R1        2.0
    X1          R2         3.0
    X2          OBJ        4.0     R1        5.0
RHS
    RHS1        R1        10.0
    RHS1        R2        20.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.objective["X1"] == 1.0
        assert problem.objective["X2"] == 4.0
        assert problem.constraints[0].coefficients.get("X1", 0) == 2.0
        assert problem.constraints[0].coefficients.get("X2", 0) == 5.0

    def test_two_rhs_per_line(self):
        """Test dos RHS por linea."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
 L  R2
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
    X1          R2         3.0
RHS
    RHS1        R1        10.0    R2        20.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.constraints[0].rhs == 10.0
        assert problem.constraints[1].rhs == 20.0

    def test_multiple_rhs_names(self):
        """Test multiples nombres RHS (usa el primero)."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
RHS
    RHS1        R1        10.0
    RHS2        R1        20.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.constraints[0].rhs == 10.0

    def test_default_nonnegativity(self):
        """Test que por defecto las variables tienen lower=0."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
RHS
    RHS1        R1         5.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.bounds["X1"].lower == 0.0

    def test_sense_mapping(self):
        """Test mapeo de sentidos de restriccion."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 E  R1
 G  R2
 L  R3
COLUMNS
    X1          OBJ        1.0
    X1          R1         1.0
    X1          R2         1.0
    X1          R3         1.0
RHS
    RHS1        R1         5.0
    RHS1        R2         6.0
    RHS1        R3         7.0
ENDATA"""
        problem = MPSParser(mps).parse()
        senses = {c.name: c.sense for c in problem.constraints}
        assert senses["R1"] == "="
        assert senses["R2"] == ">="
        assert senses["R3"] == "<="

    def test_invalid_row_type_ignored(self):
        """Test que tipo de fila invalido se ignora."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
 X  R2
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
RHS
    RHS1        R1         5.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert len(problem.constraints) == 1  # R2 ignorada

    def test_short_bound_line(self):
        """Test bound line con pocos campos."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         1.0
RHS
    RHS1        R1         5.0
BOUNDS
 LO
ENDATA"""
        problem = MPSParser(mps).parse()
        # Debe ignorar la bound mal formada
        assert problem.bounds["X1"].lower == 0.0

    def test_no_bounds_section(self):
        """Test que funciona sin seccion BOUNDS."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
COLUMNS
    X1          OBJ        1.0
    X1          R1         2.0
RHS
    RHS1        R1         5.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.bounds["X1"].lower == 0.0

    def test_ranges_two_entries(self):
        """Test RANGES con dos entradas por linea."""
        mps = """NAME          TEST
ROWS
 N  OBJ
 L  R1
 L  R2
COLUMNS
    X1          OBJ        1.0
    X1          R1         1.0
    X1          R2         1.0
RHS
    RHS1        R1         5.0
    RHS1        R2        10.0
RANGES
    RNG1        R1         3.0     R2        4.0
ENDATA"""
        problem = MPSParser(mps).parse()
        assert problem.constraints[0].rhs == 8.0  # 5 + 3
        assert problem.constraints[1].rhs == 14.0  # 10 + 4
