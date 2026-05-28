"""
Tests for LP Parser.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from src.parser.lp_parser import LPParser


class TestLPParser:
    """Tests for LPParser."""

    def test_simple_max_problem(self):
        """Test parsing a simple maximization problem."""
        txt = """
        max: 3 x + 4 y;
        x + 2 y <= 14;
        x + y <= 8;
        3 x - y >= 0;
        x + 4 y = 10;
        """
        problem = LPParser(txt).parse()
        assert problem.sense == "max"
        assert "x" in problem.objective
        assert "y" in problem.objective
        assert len(problem.constraints) == 4

    def test_integer_variable(self):
        """Test parsing integer variable type."""
        txt = """
        max: 3 x + 4 y;
        x + 2 y <= 14;
        x >= 0 integer;
        y >= 0;
        """
        problem = LPParser(txt).parse()
        assert problem.variable_types.get("x") == "integer"
        assert problem.variable_types.get("y") == "continuous"

    def test_binary_variable(self):
        """Test parsing binary variable type."""
        txt = """
        max: 3 x + 4 y;
        x + 2 y <= 14;
        x >= 0 binary;
        """
        problem = LPParser(txt).parse()
        assert problem.variable_types.get("x") == "binary"

    def test_constraint_naming(self):
        """Test auto-naming of constraints."""
        txt = """
        max: x + y;
        x + 2 y <= 10;
        2 x + 3 y >= 5;
        """
        problem = LPParser(txt).parse()
        assert any(c.name.startswith("R") for c in problem.constraints)
        assert len(problem.constraints) == 2

    def test_minimization(self):
        """Test minimization problem."""
        txt = """
        min: 2 x + 3 y;
        x + y >= 5;
        x <= 10;
        y <= 10;
        """
        problem = LPParser(txt).parse()
        assert problem.sense == "min"

    def test_empty_expression_error(self):
        """Test empty linear expression raises error."""
        with pytest.raises(ValueError, match="vacía"):
            problem = LPParser("max: 3 x + 4 y;\n x + 2 y <= 14;")
            problem._parse_linear_expression("")

    def test_invalid_sense_error(self):
        """Test invalid optimization direction."""
        with pytest.raises(ValueError, match="inválida"):
            LPParser("foo: x + y;\nx <= 10;").parse()

    def test_variable_names_with_underscores(self):
        """Test variable names with underscores and digits."""
        txt = """
        max: 3 x_1 + 4 var_2;
        x_1 + 2 var_2 <= 14;
        """
        problem = LPParser(txt).parse()
        assert "x_1" in problem.objective
        assert "var_2" in problem.objective

    def test_free_variable(self):
        """Test free/unrestricted variable."""
        txt = """
        max: x + y;
        x + y <= 10;
        x free;
        y >= 0;
        """
        problem = LPParser(txt).parse()
        assert "x" in problem.bounds
        assert problem.bounds["x"].lower is None
        assert problem.bounds["x"].upper is None

    def test_unrestricted_variable(self):
        """Test unrestricted variable keyword."""
        txt = """
        max: x + y;
        x + y <= 10;
        x unrestricted;
        y >= 0;
        """
        problem = LPParser(txt).parse()
        assert "x" in problem.bounds
        assert problem.bounds["x"].lower is None
        assert problem.bounds["x"].upper is None

    def test_double_sided_bounds(self):
        """Test double-sided bounds (0 <= x <= 10)."""
        txt = """
        max: x + y;
        x + y <= 20;
        0 <= x <= 10;
        5 <= y <= 15;
        """
        problem = LPParser(txt).parse()
        assert problem.bounds["x"].lower == 0
        assert problem.bounds["x"].upper == 10
        assert problem.bounds["y"].lower == 5
        assert problem.bounds["y"].upper == 15

    def test_single_constraint(self):
        """Test problema con una sola restriccion."""
        txt = """
        max: x;
        x + y <= 10;
        """
        problem = LPParser(txt).parse()
        assert len(problem.constraints) == 1

    def test_comment_lines(self):
        """Test that comment lines (#) are ignored."""
        txt = """
        max: x + y;
        # This is a comment
        x + y <= 10;
        # Another comment
        x + 2 y >= 5;
        """
        problem = LPParser(txt).parse()
        assert len(problem.constraints) == 2

    def test_maximize_keyword(self):
        """Test the full keyword 'maximize' retains its form."""
        txt = """
        maximize: 3 x + 4 y;
        x + 2 y <= 14;
        x + y <= 8;
        """
        problem = LPParser(txt).parse()
        assert problem.sense == "maximize"

    def test_minimize_keyword(self):
        """Test the full keyword 'minimize' retains its form."""
        txt = """
        minimize: 3 x + 4 y;
        x + 2 y <= 14;
        x + y <= 8;
        """
        problem = LPParser(txt).parse()
        assert problem.sense == "minimize"

    def test_no_constraints_raises(self):
        """Test that missing constraints raises error."""
        with pytest.raises(ValueError, match="restricción"):
            LPParser("max: x + y;").parse()

    def test_variable_names_with_digits(self):
        """Test variable names containing digits."""
        txt = """
        max: 10 var1 + 20 var2;
        var1 + var2 <= 100;
        """
        problem = LPParser(txt).parse()
        assert "var1" in problem.objective
        assert "var2" in problem.objective

    def test_semicolons_in_objective(self):
        """Test semicolon handling in objective."""
        txt = """
        max: 3 x + 4 y;
        x + 2 y <= 14;
        """
        problem = LPParser(txt).parse()
        assert problem.objective["x"] == 3.0
        assert problem.objective["y"] == 4.0

    def test_bound_equality_edge_case(self):
        """Test bound with single <= or >= for a variable."""
        txt = """
        max: x + y;
        x + y <= 10;
        x >= 5;
        y <= 8;
        """
        problem = LPParser(txt).parse()
        assert problem.bounds["x"].lower == 5
        assert problem.bounds["y"].upper == 8

    def test_empty_objective_line_raises(self):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="objetivo"):
            LPParser("").parse()

    def test_objective_without_expression_raises(self):
        """Test that objective without expression raises error."""
        with pytest.raises(ValueError, match="inválida"):
            LPParser("max:\nx + y <= 10;").parse()

    def test_invalid_constraint_format_raises(self):
        """Test that constraint without operator raises error."""
        with pytest.raises(ValueError, match="Restricción"):
            LPParser("max: x;\nx y;").parse()

    def test_invalid_rhs_raises(self):
        """Test that constraint with non-numeric RHS raises error."""
        with pytest.raises(ValueError, match="RHS|bound"):
            LPParser("max: x + y;\n2 x + 3 y <= abc;").parse()

    def test_bound_left_format(self):
        """Test bound left format: '3 <= x'."""
        txt = """
        max: x + y;
        x + y <= 20;
        10 <= x;
        5 <= y;
        """
        problem = LPParser(txt).parse()
        assert problem.bounds["x"].lower == 10
        assert problem.bounds["y"].lower == 5

    def test_invalid_bound_format_raises(self):
        """Test that invalid bound format raises error."""
        with pytest.raises(ValueError, match="bound"):
            parser = LPParser("max: x;\nx <= 10;\ninvalid_bound;")
            parser._parse_bound("invalid_bound")

    def test_uppercase_sense_detection(self):
        """Test 'MAX' keyword maps to max via partial match."""
        txt = """
        MAX: x + y;
        x + y <= 10;
        """
        problem = LPParser(txt).parse()
        assert problem.sense == "max"

    def test_mixed_case_sense_preserved(self):
        """Test 'maximizar' keyword preserved as-is (recognized directly)."""
        txt = """
        maximizar: x + y;
        x + y <= 10;
        """
        problem = LPParser(txt).parse()
        assert problem.sense == "maximizar"
