"""
Pytest configuration for test isolation.
Clean up any mock modules that may interfere with real module imports.
This runs at session start and after specific test modules.
"""

import sys
import types
from unittest.mock import MagicMock

# Clean mock modules if they exist (from test_cli/test_benchmark.py)
# These mocks interfere with actual tests for visualization and analysis modules
modules_to_clean = [
    'src.visualization',
    'src.visualization.benchmark_plots',
    'src.visualization.visualization',
    'src.analysis.benchmark_results',
    'src.analysis.benchmark_report',
]


def _patch_modules():
    def _make_func(*args, **kwargs):
        return MagicMock()

    modules = {
        "gurobipy": ["GRB", "Model", "Env", "GenConstr"],
        "highspy": ["Highs"],
        "pulp": ["LpProblem", "LpVariable", "LpMinimize", "LpMaximize",
                 "LpStatusOptimal", "LpStatus", "value", "lpSum"],
        "swiglpk": [],
        "pyscipopt": ["Model"],
        "ecos": [],
        "osqp": [],
        "cvxopt": [],
        "scs": [],
    }

    for mod_name, attrs in modules.items():
        if mod_name not in sys.modules:
            mock_mod = types.ModuleType(mod_name)
            for attr in attrs:
                setattr(mock_mod, attr, _make_func)
            sys.modules[mod_name] = mock_mod


_patch_modules()


def pytest_configure(config):
    """Run before test collection to clean mock modules."""
    for mod in modules_to_clean:
        if mod in sys.modules:
            del sys.modules[mod]
