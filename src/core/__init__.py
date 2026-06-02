"""
Core classes for the linear programming solver.
"""

from .bound import VariableBound
from .constants import (
    FEASIBILITY_TOLERANCE,
    OPTIMALITY_TOLERANCE,
)
from .constraint import LinearConstraint
from .exceptions import (
    LPError,
    LPParseError,
)
from .problem import LinearProblem
from .solution import (
    NumericalQuality,
    ProgressPoint,
    Solution,
    SolutionTable,
    to_solution_table,
)
from .verification import compare_solutions, verify_solution

__all__ = [
    "LinearProblem",
    "Solution",
    "ProgressPoint",
    "NumericalQuality",
    "SolutionTable",
    "to_solution_table",
    "LinearConstraint",
    "VariableBound",
    "FEASIBILITY_TOLERANCE",
    "OPTIMALITY_TOLERANCE",
    "verify_solution",
    "compare_solutions",
    "LPError",
    "LPParseError",
]
