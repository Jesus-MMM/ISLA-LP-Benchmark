"""
Tests para CPLEXParser.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.parser.cplex_parser import CPLEXParser


class TestCPLEXParser:
    """Tests para el parser de formato CPLEX LP."""

    def test_simple_maximize(self):
        """Test parseo de problema de maximizacion simple."""
        txt = """
Maximize
  3 x + 4 y
Subject To
  c1: x + 2 y <= 14
  c2: 3 x - y >= 0
Bounds
  0 <= x <= 10
  0 <= y <= 10
End
"""
        problem = CPLEXParser(txt).parse()
        assert problem.sense == "max"
        assert problem.objective.get("x") == 3.0
        assert problem.objective.get("y") == 4.0
        assert len(problem.constraints) == 2

    def test_minimize(self):
        """Test parseo de problema de minimizacion."""
        txt = """
Minimize
  x + y
Subject To
  c1: x + y >= 5
End
"""
        problem = CPLEXParser(txt).parse()
        assert problem.sense == "min"

    def test_subject_to_section(self):
        """Test seccion Subject To con diferentes sentidos."""
        txt = """
Maximize
  x + 2 y
Subject To
  c1: x + y <= 10
  c2: x - y >= 2
  c3: x = 5
End
"""
        problem = CPLEXParser(txt).parse()
        assert len(problem.constraints) == 3
        assert problem.constraints[0].sense == "<="
        assert problem.constraints[1].sense == ">="
        assert problem.constraints[2].sense == "="

    def test_bounds_section(self):
        """Test seccion Bounds con limites simples."""
        txt = """
Maximize
  x + y
Subject To
  c1: x + y <= 10
Bounds
  x >= 0
  x <= 100
  y >= 5
End
"""
        problem = CPLEXParser(txt).parse()
        assert "x" in problem.bounds
        assert "y" in problem.bounds
        assert problem.bounds["x"].lower == 0
        assert problem.bounds["x"].upper == 100
        assert problem.bounds["y"].lower == 5

    def test_general_integer_section(self):
        """Test seccion General/Integer."""
        txt = """
Maximize
  3 x + 4 y
Subject To
  c1: x + 2 y <= 14
Bounds
  0 <= x <= 10
  0 <= y <= 10
Integer
  x
End
"""
        problem = CPLEXParser(txt).parse()
        assert problem.variable_types.get("x") == "integer"
        assert problem.variable_types.get("y") == "continuous"

    def test_binary_section(self):
        """Test seccion Binary."""
        txt = """
Maximize
  3 x + 4 y
Subject To
  c1: x + 2 y <= 14
Bounds
  0 <= x <= 1
  0 <= y <= 1
Binary
  x
  y
End
"""
        problem = CPLEXParser(txt).parse()
        assert problem.variable_types.get("x") == "binary"
        assert problem.variable_types.get("y") == "binary"

    def test_default_problem_name(self):
        """Test nombre de problema por defecto."""
        txt = """
Maximize
  x + y
Subject To
  c1: x + y <= 10
End
"""
        problem = CPLEXParser(txt).parse()
        assert problem.name == "LPProblem"

    def test_comment_lines(self):
        """Test que lineas de comentario se ignoran."""
        txt = """
\\ This is a comment
Maximize
\\ Another comment
  x + y
Subject To
  c1: x <= 10
End
"""
        problem = CPLEXParser(txt).parse()
        assert len(problem.constraints) == 1

    def test_parse_expression_with_negative(self):
        """Test parseo de expresion con coeficientes negativos."""
        txt = """
Maximize
  3 x - 4 y + 2 z
Subject To
  c1: x + y - z <= 10
End
"""
        problem = CPLEXParser(txt).parse()
        assert problem.objective.get("x") == 3.0
        assert problem.objective.get("y") == -4.0
        assert problem.objective.get("z") == 2.0

    def test_parse_expression_without_coefficient(self):
        """Test parseo de variable sin coeficiente explicito."""
        txt = """
Maximize
  x + y
Subject To
  c1: x + 2 y <= 10
End
"""
        problem = CPLEXParser(txt).parse()
        assert problem.objective.get("x") == 1.0
        assert problem.objective.get("y") == 1.0

    def test_parse_lp_file(self):
        """Test funcion parse_lp_file."""
        import tempfile

        from src.parser.cplex_parser import parse_lp_file

        content = """
Maximize
  x + y
Subject To
  c1: x <= 10
End
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            f.flush()
            problem = parse_lp_file(f.name)
        os.unlink(f.name)
        assert problem.sense == "max"
        assert len(problem.constraints) == 1

    def test_double_sided_bounds_via_separate_lines(self):
        """Test bounds usando lineas separadas para lower y upper."""
        txt = """
Maximize
  x + y
Subject To
  c1: x + y <= 10
Bounds
  x >= 0
  x <= 5
  y >= -1
  y <= 1
End
"""
        problem = CPLEXParser(txt).parse()
        assert problem.bounds["x"].lower == 0
        assert problem.bounds["x"].upper == 5
        assert problem.bounds["y"].lower == -1
        assert problem.bounds["y"].upper == 1


