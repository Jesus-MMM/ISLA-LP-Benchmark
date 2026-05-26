"""
Tests for LP Parser.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.parser.lp_parser import LPParser


class TestLPParser:
    """Tests for LPParser."""
    
    def test_simple_max_problem(self):
        """Test parsing a simple maximization problem."""
        txt = """
        max: 3 x + 4 y;
        x + 2 y <= 14;
        x + y <= 8;
        x <= 6;
        y <= 5;
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
        max: x;
        x <= 10;
        y <= 5;
        """
        problem = LPParser(txt).parse()
        # Should have auto-generated names R0, R1
        assert any(c.name.startswith("R") for c in problem.constraints)
