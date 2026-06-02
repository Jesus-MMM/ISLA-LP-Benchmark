"""
Solution verification for LP problems.
Validates that solutions satisfy all constraints and variable bounds.
"""

from .constants import FEASIBILITY_TOLERANCE
from .problem import LinearProblem
from .solution import Solution


def verify_solution(
    problem: LinearProblem,
    solution: Solution,
    tolerance: float | None = None
) -> tuple[bool, list[str]]:
    """
    Verify that a solution satisfies all constraints and bounds.
    
    Args:
        problem: The LP problem
        solution: The solution to verify
        tolerance: Custom tolerance (uses FEASIBILITY_TOLERANCE if None)
    
    Returns:
        (is_valid, list_of_issues)
    """
    if tolerance is None:
        tolerance = FEASIBILITY_TOLERANCE

    issues = []

    if not solution.variables:
        return False, ["No variable values in solution"]

    # Check variable bounds
    for var, value in solution.variables.items():
        bound = problem.bounds.get(var)
        if bound:
            if bound.lower is not None and value < bound.lower - tolerance:
                issues.append(
                    f"Variable {var} = {value:.6f} violates lower bound {bound.lower}"
                )
            if bound.upper is not None and value > bound.upper + tolerance:
                issues.append(
                    f"Variable {var} = {value:.6f} violates upper bound {bound.upper}"
                )

    # Check constraints
    for i, constraint in enumerate(problem.constraints):
        # Evaluate LHS
        lhs = sum(
            coeff * solution.variables.get(var, 0.0)
            for var, coeff in constraint.coefficients.items()
        )

        if constraint.sense == "<=":
            if lhs > constraint.rhs + tolerance:
                issues.append(
                    f"Constraint {i} violated: {lhs:.6f} > {constraint.rhs} (slack = {constraint.rhs - lhs:.6f})"
                )
        elif constraint.sense == ">=":
            if lhs < constraint.rhs - tolerance:
                issues.append(
                    f"Constraint {i} violated: {lhs:.6f} < {constraint.rhs} (slack = {lhs - constraint.rhs:.6f})"
                )
        elif constraint.sense == "=":
            if abs(lhs - constraint.rhs) > tolerance:
                issues.append(
                    f"Constraint {i} violated: {lhs:.6f} != {constraint.rhs} (diff = {abs(lhs - constraint.rhs):.6f})"
                )

    return len(issues) == 0, issues


def compare_solutions(
    problem: LinearProblem,
    solutions: list[Solution],
    tolerance: float | None = None
) -> list[str]:
    """
    Compare multiple solutions for the same problem.
    
    Args:
        problem: The LP problem
        solutions: List of solutions to compare
        tolerance: Custom tolerance
        
    Returns:
        List of warning messages if solutions disagree
    """
    if tolerance is None:
        tolerance = FEASIBILITY_TOLERANCE

    warnings = []

    # Filter optimal solutions
    optimal_solutions = [s for s in solutions if s.is_optimal()]

    if len(optimal_solutions) < 2:
        return warnings

    # Compare objective values
    obj_values = [s.objective_value for s in optimal_solutions if s.objective_value is not None]

    if len(obj_values) >= 2:
        max_obj = max(obj_values)
        min_obj = min(obj_values)

        if max_obj - min_obj > tolerance * (1 + abs(max_obj)):
            warnings.append(
                f"Objective values differ by {max_obj - min_obj:.6f}. "
                f"Range: [{min_obj:.6f}, {max_obj:.6f}]"
            )

    return warnings
