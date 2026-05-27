"""
Validador de problemas de programación lineal.
"""

from dataclasses import dataclass, field
from typing import Optional

from ..core import LinearProblem


@dataclass
class ValidationIssue:
    """Representa un problema de validación encontrado."""
    severity: str  # ERROR, WARNING
    code: str
    message: str
    location: Optional[str] = None  # "objective", "constraint", "bound", etc.
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None


@dataclass
class ValidationResult:
    """Resultado de la validación de un problema de PL."""
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Verifica si hay errores."""
        return any(i.severity == "ERROR" for i in self.issues)

    def has_warnings(self) -> bool:
        """Verifica si hay advertencias."""
        return any(i.severity == "WARNING" for i in self.issues)

    def get_errors(self) -> list[ValidationIssue]:
        """Retorna solo los errores."""
        return [i for i in self.issues if i.severity == "ERROR"]

    def get_warnings(self) -> list[ValidationIssue]:
        """Retorna solo las advertencias."""
        return [i for i in self.issues if i.severity == "WARNING"]

    def summary(self) -> str:
        """Genera un resumen de la validación."""
        if self.is_valid and not self.issues:
            return "El problema es válido."
        
        lines = []
        if self.has_errors():
            lines.append(f"ERRORES ({len(self.get_errors())}):")
            for issue in self.get_errors():
                lines.append(f"  - [{issue.code}] {issue.message}")
        
        if self.has_warnings():
            lines.append(f"ADVERTENCIAS ({len(self.get_warnings())}):")
            for issue in self.get_warnings():
                lines.append(f"  - [{issue.code}] {issue.message}")
        
        return "\n".join(lines)


def validate_problem(problem: LinearProblem) -> ValidationResult:
    """
    Valida un problema de programación lineal.

    Args:
        problem: LinearProblem - El problema a validar.

    Returns:
        ValidationResult: Resultado con losIssues encontrados.
    """
    issues: list[ValidationIssue] = []

    issues.extend(_validate_objective(problem))
    issues.extend(_validate_constraints(problem))
    issues.extend(_validate_variables(problem))
    issues.extend(_validate_bounds(problem))

    is_valid = not any(i.severity == "ERROR" for i in issues)

    return ValidationResult(is_valid=is_valid, issues=issues)


def _validate_objective(problem: LinearProblem) -> list[ValidationIssue]:
    """Valida la función objetivo."""
    issues: list[ValidationIssue] = []

    if not problem.objective:
        issues.append(ValidationIssue(
            severity="ERROR",
            code="VAL-001",
            message="La función objetivo no puede estar vacía",
            location="objective"
        ))
        return issues

    if not problem.variables:
        issues.append(ValidationIssue(
            severity="ERROR",
            code="VAL-001",
            message="No hay variables definidas",
            location="objective"
        ))
        return issues

    obj_vars = set(problem.objective.keys())
    problem_vars = set(problem.variables)

    vars_not_in_problem = obj_vars - problem_vars
    if vars_not_in_problem:
        issues.append(ValidationIssue(
            severity="WARNING",
            code="VAL-005",
            message=f"Variables en objetivo no definidas: {vars_not_in_problem}",
            location="objective"
        ))

    zero_coeffs = [v for v, c in problem.objective.items() if c == 0]
    if zero_coeffs:
        issues.append(ValidationIssue(
            severity="WARNING",
            code="VAL-005",
            message=f"Variables con coeficiente cero: {zero_coeffs}",
            location="objective"
        ))

    return issues


def _validate_constraints(problem: LinearProblem) -> list[ValidationIssue]:
    """Valida las restricciones."""
    issues: list[ValidationIssue] = []

    if not problem.constraints:
        issues.append(ValidationIssue(
            severity="ERROR",
            code="VAL-001",
            message="Se requiere al menos una restricción",
            location="constraints"
        ))
        return issues

    for i, constraint in enumerate(problem.constraints):
        loc = f"constraint_{i}"

        if not constraint.coefficients:
            issues.append(ValidationIssue(
                severity="ERROR",
                code="VAL-003",
                message=f"Restricción {i} sin coeficientes",
                location=loc
            ))
            continue

        constraint_vars = set(constraint.coefficients.keys())
        problem_vars = set(problem.variables)

        vars_not_in_problem = constraint_vars - problem_vars
        if vars_not_in_problem:
            issues.append(ValidationIssue(
                severity="ERROR",
                code="VAL-005",
                message=f"Restricción {i}: variables no definidas: {vars_not_in_problem}",
                location=loc
            ))

        if constraint.sense not in ("<=", ">=", "="):
            issues.append(ValidationIssue(
                severity="ERROR",
                code="PARSE-003",
                message=f"Restricción {i}: sentido inválido '{constraint.sense}'",
                location=loc
            ))

    return issues


def _validate_variables(problem: LinearProblem) -> list[ValidationIssue]:
    """Valida las variables."""
    issues: list[ValidationIssue] = []

    if not problem.variables:
        issues.append(ValidationIssue(
            severity="ERROR",
            code="VAL-001",
            message="No hay variables definidas",
            location="variables"
        ))
        return issues

    if len(problem.variables) > 1000:
        issues.append(ValidationIssue(
            severity="WARNING",
            code="VAL-005",
            message=f"El problema tiene {len(problem.variables)} variables (puede ser lento)",
            location="variables"
        ))

    seen = set()
    duplicate_vars = set()
    for v in problem.variables:
        if v in seen:
            duplicate_vars.add(v)
        seen.add(v)
    if duplicate_vars:
        issues.append(ValidationIssue(
            severity="ERROR",
            code="VAL-002",
            message=f"Variables duplicadas: {duplicate_vars}",
            location="variables"
        ))

    return issues


def _validate_bounds(problem: LinearProblem) -> list[ValidationIssue]:
    """Valida los límites de las variables."""
    issues: list[ValidationIssue] = []

    for var, bound in problem.bounds.items():
        loc = f"bound_{var}"

        if bound.lower is not None and bound.upper is not None:
            if bound.lower > bound.upper:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    code="VAL-004",
                    message=f"Variable {var}: límite inferior ({bound.lower}) > límite superior ({bound.upper})",
                    location=loc
                ))

        if bound.lower is not None and bound.lower == bound.upper:
            issues.append(ValidationIssue(
                severity="WARNING",
                code="VAL-004",
                message=f"Variable {var}: límite inferior = superior (variable fija)",
                location=loc
            ))

    unbound_vars = [
        v for v in problem.variables
        if v not in problem.bounds or (
            problem.bounds[v].lower is None and 
            problem.bounds[v].upper is None
        )
    ]
    if unbound_vars:
        issues.append(ValidationIssue(
            severity="WARNING",
            code="VAL-005",
            message=f"Variables sin límites explícitos (se usará no negatividad): {unbound_vars[:5]}{'...' if len(unbound_vars) > 5 else ''}",
            location="bounds"
        ))

    return issues