"""
Tests para cli/__init__.py - get_system_info y format_system_report.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cli import get_system_info, format_system_report


class TestGetSystemInfo:
    """Tests para get_system_info."""

    def test_returns_dict(self):
        info = get_system_info()
        assert isinstance(info, dict)

    def test_has_platform_key(self):
        info = get_system_info()
        assert "platform" in info

    def test_platform_has_keys(self):
        info = get_system_info()
        platform = info.get("platform", {})
        assert "system" in platform
        assert "release" in platform
        assert "python_version" in platform

    def test_has_hostname(self):
        info = get_system_info()
        assert "hostname" in info

    def test_has_timestamp(self):
        info = get_system_info()
        assert "timestamp" in info


class TestFormatSystemReport:
    """Tests para format_system_report."""

    def test_format_basic(self):
        info = {
            "platform": {
                "system": "Windows",
                "release": "10",
                "machine": "AMD64",
                "processor": "Intel",
                "python_version": "3.12.0",
            },
            "hostname": "test-host",
            "timestamp": "2024-01-01T00:00:00",
        }
        report = format_system_report(info)
        assert "Sistema: Windows" in report
        assert "Windows" in report

    def test_format_missing_platform(self):
        info = {"hostname": "test"}
        report = format_system_report(info)
        assert "N/A" in report

    def test_format_missing_hostname(self):
        info = {
            "platform": {
                "system": "Linux",
                "release": "5.0",
                "machine": "x86_64",
                "processor": "CPU",
                "python_version": "3.11.0",
            },
            "timestamp": "2024-01-01",
        }
        report = format_system_report(info)
        assert "Hostname" in report

    def test_format_empty_info(self):
        info = {}
        report = format_system_report(info)
        assert "Sistema:" in report