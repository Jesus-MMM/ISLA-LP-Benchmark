"""
Tests para MultiLPParser.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest

from src.parser.multi_parser import MultiLPParser


class TestMultiLPParser:
    """Tests para el parser de multiples problemas LP."""

    def test_parse_two_problems(self):
        """Test parseo de dos problemas separados por ---."""
        txt = """
max: 3 x + 4 y;
x + 2 y <= 14;
x + y <= 8;

---
min: 2 a + 3 b;
a + b >= 5;
a + b <= 10;
"""
        parser = MultiLPParser(txt)
        problems = parser.parse_all()
        assert len(problems) == 2

    def test_problem_names(self):
        """Test nombres de problemas auto-generados."""
        txt = """
max: x + y;
x + 2 y <= 10;

---
max: a + b;
a + b <= 5;
"""
        problems = MultiLPParser(txt).parse_all()
        assert problems[0].name == "Problema 1"
        assert problems[1].name == "Problema 2"

    def test_count_problems(self):
        """Test count_problems metodo estatico."""
        txt = """
max: x + y;
x + y <= 10;

---
max: a + b;
a + b <= 5;

---
min: p + q;
p + q >= 0;
"""
        count = MultiLPParser.count_problems(txt)
        assert count == 3

    def test_empty_sections(self):
        """Test manejo de secciones vacias entre delimitadores."""
        txt = """
max: x + y;
x + y <= 10;

---

---
max: a + b;
a + b <= 5;
"""
        problems = MultiLPParser(txt).parse_all()
        assert len(problems) >= 1

    def test_comment_lines(self):
        """Test lineas de comentario ignoradas."""
        txt = """
# Problema de prueba 1
max: 3 x + 4 y;
x + 2 y <= 14;

---
# Problema de prueba 2
max: a + b;
a + b <= 10;
"""
        parser = MultiLPParser(txt)
        problems = parser.parse_all()
        assert len(problems) == 2

    def test_single_problem(self):
        """Test con un solo problema (sin delimitador)."""
        txt = """
max: 3 x + 4 y;
x + 2 y <= 14;
x + y <= 8;
"""
        problems = MultiLPParser(txt).parse_all()
        assert len(problems) == 1

    def test_count_single_problem(self):
        """Test count_problems con un solo problema."""
        txt = """
max: x + y;
x + y <= 10;
"""
        count = MultiLPParser.count_problems(txt)
        assert count == 1

    def test_count_empty_text(self):
        """Test count_problems con texto vacio."""
        assert MultiLPParser.count_problems("") == 0

    def test_count_with_comments(self):
        """Test count_problems ignora secciones solo comentarios."""
        txt = """
# Solo comentarios
# Otro comentario

---
max: x + y;
x + y <= 10;
"""
        count = MultiLPParser.count_problems(txt)
        assert count == 1

    def test_three_delimiter_styles(self):
        """Test los tres estilos de delimitadores."""
        txt = """
max: x + y;
x + y <= 10;
===
max: a + b;
a + b <= 5;
___
max: p + q;
p + q <= 1;
"""
        problems = MultiLPParser(txt).parse_all()
        assert len(problems) == 3

    def test_parse_all_returns_list(self):
        """Test parse_all retorna lista."""
        result = MultiLPParser("max: x + y\nx + y <= 10\n").parse_all()
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_invalid_problem_raises(self):
        """Test que problemas invalidos lanzan LPParseError."""
        from src.core.exceptions import LPParseError
        txt = """
max: x + y;
x + y <= 10;

---

esto no es un problema valido

---
max: a + b;
a + b <= 5;
"""
        with pytest.raises(LPParseError, match="problema 2"):
            MultiLPParser(txt).parse_all()
