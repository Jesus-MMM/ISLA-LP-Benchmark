"""
Tests para validacion de problemas de PL.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.problem import LinearProblem
from src.core.constraint import LinearConstraint
from src.core.bound import VariableBound
from src.utils.validation import (
    validate_problem,
    ValidationResult,
    ValidationIssue,
)


class TestValidateProblem:
    """Tests para validate_problem."""

    def test_valid_problem(self):
        """Test problema valido retorna is_valid=True."""
        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1, "y": 1}, rhs=10, sense="<="),
            ],
            variables=["x", "y"],
            bounds={
                "x": VariableBound("x", lower=0, upper=10),
                "y": VariableBound("y", lower=0, upper=10),
            },
        )
        result = validate_problem(problem)
        assert result.is_valid

    def test_missing_objective(self):
        """Test problema sin objetivo."""
        problem = LinearProblem(
            objective={},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<="),
            ],
            variables=["x"],
            bounds={},
        )
        result = validate_problem(problem)
        assert not result.is_valid
        assert any(i.code == "VAL-001" for i in result.issues)

    def test_no_variables(self):
        """Test problema sin variables."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=[],
            bounds={},
        )
        result = validate_problem(problem)
        assert not result.is_valid
        codes = [i.code for i in result.issues]
        assert "VAL-001" in codes

    def test_duplicate_variables(self):
        """Test variables duplicadas."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x", "x"],
            bounds={},
        )
        result = validate_problem(problem)
        # duplicate detection depends on validation
        assert any(i.code == "VAL-002" for i in result.issues)

    def test_inconsistent_bounds(self):
        """Test bounds inconsistentes (lower > upper)."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={"x": VariableBound("x", lower=10, upper=5)},
        )
        result = validate_problem(problem)
        assert not result.is_valid
        assert any(i.code == "VAL-004" for i in result.issues)

    def test_no_constraints(self):
        """Test problema sin restricciones."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        result = validate_problem(problem)
        assert not result.is_valid
        assert any(i.code == "VAL-001" for i in result.issues)

    def test_invalid_sense_in_constraint(self):
        """Test restriccion con sentido invalido."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<>"),
            ],
            variables=["x"],
            bounds={},
        )
        result = validate_problem(problem)
        assert not result.is_valid
        assert any(i.code == "PARSE-003" for i in result.issues)

    def test_variables_not_in_problem(self):
        """Test variables en objetivo no definidas en variables list."""
        problem = LinearProblem(
            objective={"x": 1, "z": 2},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        result = validate_problem(problem)
        assert any(i.code == "VAL-005" for i in result.issues)


    def test_zero_coefficient_warning(self):
        """Test advertencia por coeficiente cero en objetivo."""
        problem = LinearProblem(
            objective={"x": 1, "y": 0},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<="),
            ],
            variables=["x", "y"],
            bounds={},
        )
        result = validate_problem(problem)
        assert any(i.code == "VAL-005" for i in result.issues)

    def test_fixed_variable_warning(self):
        """Test advertencia por variable fija (lower == upper)."""
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[
                LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<="),
            ],
            variables=["x"],
            bounds={"x": VariableBound("x", lower=5, upper=5)},
        )
        result = validate_problem(problem)
        assert any(i.code == "VAL-004" for i in result.issues)


class TestValidationResult:
    """Tests para ValidationResult."""

    def test_has_errors(self):
        """Test has_errors retorna True si hay errores."""
        result = ValidationResult(
            is_valid=False,
            issues=[ValidationIssue(severity="ERROR", code="ERR", message="error")],
        )
        assert result.has_errors()

    def test_has_warnings(self):
        """Test has_warnings retorna True si hay advertencias."""
        result = ValidationResult(
            is_valid=True,
            issues=[ValidationIssue(severity="WARNING", code="WARN", message="warning")],
        )
        assert result.has_warnings()

    def test_get_errors(self):
        """Test get_errors filtra solo errores."""
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(severity="ERROR", code="E1", message="err1"),
                ValidationIssue(severity="WARNING", code="W1", message="warn1"),
            ],
        )
        errors = result.get_errors()
        assert len(errors) == 1
        assert errors[0].code == "E1"

    def test_get_warnings(self):
        """Test get_warnings filtra solo advertencias."""
        result = ValidationResult(
            is_valid=True,
            issues=[
                ValidationIssue(severity="ERROR", code="E1", message="err1"),
                ValidationIssue(severity="WARNING", code="W1", message="warn1"),
            ],
        )
        warnings = result.get_warnings()
        assert len(warnings) == 1
        assert warnings[0].code == "W1"

    def test_summary_valid(self):
        """Test summary para problema valido."""
        result = ValidationResult(is_valid=True)
        assert "válido" in result.summary()

    def test_summary_with_issues(self):
        """Test summary con issues."""
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(severity="ERROR", code="E1", message="error msg"),
            ],
        )
        summary = result.summary()
        assert "ERROR" in summary or "error" in summary


class TestValidationIssue:
    """Tests para ValidationIssue."""

    def test_creation(self):
        """Test creacion de ValidationIssue."""
        issue = ValidationIssue(severity="ERROR", code="TEST", message="test msg", location="objective")
        assert issue.severity == "ERROR"
        assert issue.code == "TEST"
        assert issue.message == "test msg"
        assert issue.location == "objective"

    def test_default_location(self):
        """Test location por defecto es None."""
        issue = ValidationIssue(severity="WARNING", code="W", message="w")
        assert issue.location is None
