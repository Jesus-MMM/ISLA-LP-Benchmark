"""
Tests para excepciones personalizadas del modulo LP.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.exceptions import (
    LPError,
    LPParseError,
    LPInfeasibleError,
    LPUnboundedError,
    LPUnsolvedError,
    LPVisualizationError,
    LPConfigurationError,
)


class TestLPError:
    """Tests para la excepcion base LPError."""

    def test_base_exception(self):
        """Test creacion y herencia de LPError."""
        err = LPError("mensaje")
        assert isinstance(err, Exception)
        assert str(err) == "mensaje"
        assert err.problem is None

    def test_base_with_problem(self):
        """Test LPError con nombre de problema."""
        err = LPError("mensaje", problem="test_problem")
        assert err.problem == "test_problem"


class TestLPParseError:
    """Tests para LPParseError."""

    def test_parse_error(self):
        """Test creacion de LPParseError."""
        err = LPParseError("formato invalido")
        assert isinstance(err, LPError)
        assert "formato invalido" in str(err)
        assert err.line is None

    def test_parse_error_with_line(self):
        """Test LPParseError con numero de linea."""
        err = LPParseError("formato invalido", line=5)
        assert err.line == 5
        assert "línea 5" in str(err) or "linea 5" in str(err)

    def test_parse_error_with_problem(self):
        """Test LPParseError con nombre de problema."""
        err = LPParseError("formato invalido", problem="prob1")
        assert err.problem == "prob1"


class TestLPInfeasibleError:
    """Tests para LPInfeasibleError."""

    def test_infeasible(self):
        """Test creacion de LPInfeasibleError."""
        err = LPInfeasibleError()
        assert isinstance(err, LPError)
        assert "infactible" in str(err).lower()

    def test_infeasible_with_problem(self):
        """Test LPInfeasibleError con nombre de problema."""
        err = LPInfeasibleError(problem="prob1")
        assert err.problem == "prob1"


class TestLPUnboundedError:
    """Tests para LPUnboundedError."""

    def test_unbounded(self):
        """Test creacion de LPUnboundedError."""
        err = LPUnboundedError()
        assert isinstance(err, LPError)
        assert "acotado" in str(err).lower()

    def test_unbounded_with_problem(self):
        """Test LPUnboundedError con nombre de problema."""
        err = LPUnboundedError(problem="prob1")
        assert err.problem == "prob1"


class TestLPUnsolvedError:
    """Tests para LPUnsolvedError."""

    def test_unsolved_default(self):
        """Test LPUnsolvedError con mensaje por defecto."""
        err = LPUnsolvedError()
        assert isinstance(err, LPError)
        assert "resuelto" in str(err).lower()

    def test_unsolved_custom(self):
        """Test LPUnsolvedError con mensaje personalizado."""
        err = LPUnsolvedError("aun no resuelto")
        assert str(err) == "aun no resuelto"


class TestLPVisualizationError:
    """Tests para LPVisualizationError."""

    def test_visualization_error(self):
        """Test creacion de LPVisualizationError."""
        err = LPVisualizationError("grafico fallo")
        assert isinstance(err, LPError)
        assert "visualización" in str(err) or "visualizacion" in str(err)
        assert "grafico fallo" in str(err)


class TestLPConfigurationError:
    """Tests para LPConfigurationError."""

    def test_configuration_error(self):
        """Test creacion de LPConfigurationError."""
        err = LPConfigurationError("config invalida")
        assert isinstance(err, LPError)
        assert "configuración" in str(err) or "configuracion" in str(err)
        assert "config invalida" in str(err)


class TestInheritanceHierarchy:
    """Tests para la jerarquia de herencia."""

    def test_all_are_lp_errors(self):
        """Test que todas las excepciones heredan de LPError."""
        assert issubclass(LPParseError, LPError)
        assert issubclass(LPInfeasibleError, LPError)
        assert issubclass(LPUnboundedError, LPError)
        assert issubclass(LPUnsolvedError, LPError)
        assert issubclass(LPVisualizationError, LPError)
        assert issubclass(LPConfigurationError, LPError)

    def test_all_are_exceptions(self):
        """Test que todas heredan de Exception."""
        assert issubclass(LPError, Exception)

    def test_catch_base(self):
        """Test que capturar LPError atrapa todas las subclases."""
        errors = [
            LPParseError("test"),
            LPInfeasibleError(),
            LPUnboundedError(),
            LPUnsolvedError(),
            LPVisualizationError("test"),
            LPConfigurationError("test"),
        ]
        for err in errors:
            assert isinstance(err, LPError)
