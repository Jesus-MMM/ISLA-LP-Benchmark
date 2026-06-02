"""
Core classes for the linear programming solver.
"""

from .problem import LinearProblem
from .solution import (
    Solution,
    ProgressPoint,
    NumericalQuality,
    SolutionTable,
    to_solution_table,
)
from .constraint import LinearConstraint
from .bound import VariableBound
from .constants import (
    FEASIBILITY_TOLERANCE,
    OPTIMALITY_TOLERANCE,
)
from .verification import verify_solution, compare_solutions
from .exceptions import (
    LPError,
    LPParseError,
)

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