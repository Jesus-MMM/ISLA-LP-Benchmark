"""
This module contains the LPParser class, which is responsible for
parsing linear programming problems from a text representation.
The parser can handle objective functions, constraints, and
variable bounds, and it converts them into a structured format
that can be used by optimization solvers like Gurobi.
"""

from .cplex_parser import CPLEXParser, parse_lp_file
from .lp_parser import LPParser
from .mps_parser import MPSParser
from .multi_parser import MultiLPParser


def detect_parser(content: str, file_ext: str = "") -> str:
    """Detecta el parser más adecuado según el contenido y la extensión."""
    ext = file_ext.lower()
    if ext == ".mps" or content.strip().startswith("NAME"):
        return "mps"
    if ext == ".lp":
        if any(kw in content for kw in ["Maximize", "Minimize", "Subject To", "End"]):
            return "cplex"
        return "lp"
    if any(kw in content for kw in ["Maximize", "Minimize", "Subject To", "End"]):
        return "cplex"
    return "lp"


def get_parser_class(parser_name: str, content: str = "", file_ext: str = "") -> type:
    """Resuelve un nombre de parser a su clase, con auto-detección."""
    if parser_name == "auto":
        parser_name = detect_parser(content, file_ext)
    return {
        "lp": LPParser,
        "cplex": CPLEXParser,
        "mps": MPSParser,
    }[parser_name]


__all__ = [
    "LPParser", "MultiLPParser", "MPSParser", "CPLEXParser", "parse_lp_file",
    "detect_parser", "get_parser_class",
]
