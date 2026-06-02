"""
Tests para VariableBound.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.bound import VariableBound


class TestVariableBound:
    """Tests para la clase VariableBound."""

    def test_creation_defaults(self):
        """Test creacion con valores por defecto."""
        b = VariableBound("x")
        assert b.variable == "x"
        assert b.lower is None
        assert b.upper is None
        assert b.variable_type == "continuous"

    def test_creation_with_bounds(self):
        """Test creacion con limites explicitos."""
        b = VariableBound("y", lower=0.0, upper=10.0)
        assert b.lower == 0.0
        assert b.upper == 10.0

    def test_is_valid_basic(self):
        """Test validacion basica de limites."""
        b = VariableBound("x", lower=0, upper=10)
        assert b.is_valid()

    def test_is_valid_lower_greater_than_upper(self):
        """Test que lower > upper devuelve invalido."""
        b = VariableBound("x", lower=10, upper=5)
        assert not b.is_valid()

    def test_is_valid_none_lower(self):
        """Test validacion con lower=None."""
        b = VariableBound("x", lower=None, upper=10)
        assert b.is_valid()

    def test_is_valid_none_upper(self):
        """Test validacion con upper=None."""
        b = VariableBound("x", lower=0, upper=None)
        assert b.is_valid()

    def test_is_valid_both_none(self):
        """Test validacion con ambos limites en None."""
        b = VariableBound("x", lower=None, upper=None)
        assert b.is_valid()

    def test_binary_valid(self):
        """Test variable binaria con limites validos [0,1]."""
        b = VariableBound("x", lower=0, upper=1, variable_type="binary")
        assert b.is_valid()

    def test_binary_lower_negative(self):
        """Test variable binaria con lower negativo."""
        b = VariableBound("x", lower=-1, upper=1, variable_type="binary")
        assert not b.is_valid()

    def test_binary_upper_gt_one(self):
        """Test variable binaria con upper > 1."""
        b = VariableBound("x", lower=0, upper=2, variable_type="binary")
        assert not b.is_valid()

    def test_binary_no_bounds(self):
        """Test variable binaria sin limites explicitos."""
        b = VariableBound("x", variable_type="binary")
        assert b.is_valid()

    def test_integer_bounds(self):
        """Test variable integer con limites."""
        b = VariableBound("x", lower=0, upper=100, variable_type="integer")
        assert b.is_valid()
        assert b.variable_type == "integer"

    def test_variable_type_property(self):
        """Test property variable_type."""
        b = VariableBound("x", variable_type="binary")
        assert b.variable_type == "binary"
        b2 = VariableBound("y", variable_type="integer")
        assert b2.variable_type == "integer"
        b3 = VariableBound("z")
        assert b3.variable_type == "continuous"

    def test_equal_bounds(self):
        """Test limites iguales (variable fija)."""
        b = VariableBound("x", lower=5, upper=5)
        assert b.is_valid()
