"""
Tests para el modulo de logging.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import logging

from src.utils.logging import LogLevel, get_logger, set_default_level


class TestLogLevel:
    """Tests para el enum LogLevel."""

    def test_debug_value(self):
        """Test que DEBUG tiene el valor correcto."""
        assert LogLevel.DEBUG.value == logging.DEBUG

    def test_info_value(self):
        """Test que INFO tiene el valor correcto."""
        assert LogLevel.INFO.value == logging.INFO

    def test_warning_value(self):
        """Test que WARNING tiene el valor correcto."""
        assert LogLevel.WARNING.value == logging.WARNING

    def test_error_value(self):
        """Test que ERROR tiene el valor correcto."""
        assert LogLevel.ERROR.value == logging.ERROR

    def test_critical_value(self):
        """Test que CRITICAL tiene el valor correcto."""
        assert LogLevel.CRITICAL.value == logging.CRITICAL

    def test_enum_members(self):
        """Test cantidad de miembros del enum."""
        members = list(LogLevel)
        assert len(members) == 5


class TestGetLogger:
    """Tests para get_logger."""

    def test_get_logger_returns_logger(self):
        """Test que get_logger retorna un Logger."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_default_level(self):
        """Test que get_logger tiene nivel por defecto WARNING."""
        logger = get_logger("test_default")
        assert logger.level == logging.WARNING

    def test_get_logger_custom_level(self):
        """Test que get_logger acepta nivel personalizado."""
        logger = get_logger("test_debug", level=LogLevel.DEBUG)
        assert logger.level == logging.DEBUG

    def test_get_logger_reuses_logger(self):
        """Test que el mismo nombre retorna el mismo logger."""
        logger1 = get_logger("test_reuse")
        logger2 = get_logger("test_reuse")
        assert logger1 is logger2


class TestSetDefaultLevel:
    """Tests para set_default_level."""

    def test_set_default_level_changes_behavior(self):
        """Test que cambiar el nivel por defecto afecta nuevos loggers."""
        set_default_level(LogLevel.DEBUG)
        logger = get_logger("test_after_change")
        assert logger.level == logging.DEBUG
        set_default_level(LogLevel.WARNING)

    def test_set_default_level_info(self):
        """Test que set_default_level con INFO funciona."""
        set_default_level(LogLevel.INFO)
        logger = get_logger("test_info")
        assert logger.level == logging.INFO
        set_default_level(LogLevel.WARNING)

    def test_set_default_level_error(self):
        """Test que set_default_level con ERROR funciona."""
        set_default_level(LogLevel.ERROR)
        logger = get_logger("test_error")
        assert logger.level == logging.ERROR
        set_default_level(LogLevel.WARNING)
