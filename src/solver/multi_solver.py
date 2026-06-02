"""
Multiple linear programming problem solver.
"""

import time
from dataclasses import dataclass, field

from ..core import LinearProblem, Solution
from ..parser import MultiLPParser
from .base import BaseSolver, SolverRegistry


@dataclass
class ProblemResult:
    """Result of solving an individual problem."""
    problem: LinearProblem
    solution: Solution
    parse_time: float = 0.0
    build_time: float = 0.0
    solve_time: float = 0.0
    total_time: float = 0.0
    error: str | None = None


@dataclass
class MultiSolverResult:
    """Result of solving multiple problems."""
    results: list[ProblemResult] = field(default_factory=list)
    total_parse_time: float = 0.0
    total_build_time: float = 0.0
    total_solve_time: float = 0.0
    total_time: float = 0.0
    verbose: bool = False
    solver_name: str = "unknown"

    def get_successful_results(self) -> list[ProblemResult]:
        return [r for r in self.results if r.error is None]

    def get_failed_results(self) -> list[ProblemResult]:
        return [r for r in self.results if r.error is not None]


class MultiSolver:
    """Solver for multiple linear programming problems."""

    def __init__(self, solver_name: str = "gurobi", verbose: bool = False):
        """
        Initialize the multi-solver.

        Args:
            solver_name: Name of the solver to use (from registry).
            verbose: If True, print detailed solver output (default False)
        """
        self.verbose = verbose
        self.solver_name = solver_name
        solver_class = SolverRegistry.get(solver_name)
        if solver_class is None:
            raise ValueError(f"Solver '{solver_name}' no encontrado en el registro")
        self._solver_class = solver_class

    def solve_all(self, problems: list[LinearProblem], time_limit: float | None = None) -> MultiSolverResult:
        """
        Solve all given problems.

        Args:
            problems: Problems to solve.
            time_limit: Optional time limit per problem in seconds.

        Returns:
            MultiSolverResult with results for each problem.
        """
        result = MultiSolverResult(verbose=self.verbose, solver_name=self.solver_name)
        overall_start = time.perf_counter()

        config = BaseSolver.Config(verbose=self.verbose, time_limit=time_limit)

        for i, problem in enumerate(problems):
            problem_result = self._solve_single(problem, config, i + 1)
            result.results.append(problem_result)
            result.total_solve_time += problem_result.solve_time

        result.total_time = time.perf_counter() - overall_start
        return result

    def _solve_single(
        self, problem: LinearProblem, config: BaseSolver.Config, index: int
    ) -> ProblemResult:
        result = ProblemResult(problem=problem, solution=Solution(
            status="",
            objective_value=None,
            variables={}
        ))

        try:
            solve_start = time.perf_counter()
            try:
                solver = self._solver_class(problem, config)
            except TypeError:
                solver = self._solver_class(problem)
                solver.config = config
            solution = solver.solve()
            result.solution = solution
            result.solve_time = time.perf_counter() - solve_start

        except Exception as e:
            result.error = str(e)
            result.solution.status = f"ERROR: {e}"

        return result

    @staticmethod
    def solve_from_text(text: str, solver_name: str = "gurobi", verbose: bool = False) -> MultiSolverResult:
        """
        Parse and solve multiple problems from text.

        Args:
            text: Text with multiple problems separated by delimiters.
            solver_name: Name of the solver to use.
            verbose: If True, print detailed solver output.

        Returns:
            MultiSolverResult with results.
        """
        overall_start = time.perf_counter()

        parse_start = time.perf_counter()
        parser = MultiLPParser(text)
        problems = parser.parse_all()
        parse_time = time.perf_counter() - parse_start

        if not problems:
            result = MultiSolverResult(verbose=verbose, solver_name=solver_name)
            result.total_time = time.perf_counter() - overall_start
            return result

        solver = MultiSolver(solver_name=solver_name, verbose=verbose)
        result = solver.solve_all(problems)
        result.total_parse_time = parse_time

        return result
