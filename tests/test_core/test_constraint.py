"""
Tests para LinearConstraint.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.constraint import LinearConstraint


class TestLinearConstraint:
    """Tests para la clase LinearConstraint."""

    def test_creation(self):
        """Test creacion basica."""
        c = LinearConstraint(coefficients={"x": 1, "y": 2}, rhs=10, sense="<=")
        assert c.coefficients == {"x": 1, "y": 2}
        assert c.rhs == 10
        assert c.sense == "<="
        assert c.name == ""

    def test_creation_with_name(self):
        """Test creacion con nombre."""
        c = LinearConstraint(coefficients={"x": 1}, rhs=5, sense=">=", name="c1")
        assert c.name == "c1"

    def test_sense_less_equal(self):
        """Test sentido <=."""
        c = LinearConstraint(coefficients={"x": 1}, rhs=0, sense="<=")
        assert c.sense == "<="

    def test_sense_greater_equal(self):
        """Test sentido >=."""
        c = LinearConstraint(coefficients={"x": 1}, rhs=0, sense=">=")
        assert c.sense == ">="

    def test_sense_equal(self):
        """Test sentido =."""
        c = LinearConstraint(coefficients={"x": 1}, rhs=0, sense="=")
        assert c.sense == "="

    def test_empty_coefficients(self):
        """Test coeficientes vacios."""
        c = LinearConstraint(coefficients={}, rhs=0, sense="<=")
        assert c.coefficients == {}

    def test_single_variable(self):
        """Test restriccion con una sola variable."""
        c = LinearConstraint(coefficients={"x": 3.5}, rhs=2.0, sense="<=")
        assert c.coefficients == {"x": 3.5}
        assert c.rhs == 2.0

    def test_multiple_variables(self):
        """Test restriccion con multiples variables."""
        c = LinearConstraint(
            coefficients={"x": 1, "y": 2, "z": -3},
            rhs=7,
            sense=">=",
            name="multi"
        )
        assert len(c.coefficients) == 3
        assert c.coefficients["z"] == -3

    def test_float_rhs(self):
        """Test rhs como float."""
        c = LinearConstraint(coefficients={"x": 1}, rhs=1.5, sense="=")
        assert c.rhs == 1.5

    def test_negative_rhs(self):
        """Test rhs negativo."""
        c = LinearConstraint(coefficients={"x": 1}, rhs=-5, sense="<=")
        assert c.rhs == -5

    def test_mutable_coefficients(self):
        """Test que coefficients es mutable."""
        c = LinearConstraint(coefficients={"x": 1}, rhs=0, sense="<=")
        c.coefficients["y"] = 2
        assert "y" in c.coefficients
