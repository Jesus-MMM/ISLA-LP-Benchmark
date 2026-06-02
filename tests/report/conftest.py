import sys
import types

import pytest


@pytest.fixture(autouse=True)
def _patch_dependencies(monkeypatch):
    """Patch problematic dependencies for testing."""
    gurobipy_mock = types.ModuleType("gurobipy")
    gurobipy_mock.GRB = types.SimpleNamespace()
    gurobipy_mock.Model = type("Model", (), {})
    gurobipy_mock.Env = type("Env", (), {})
    sys.modules["gurobipy"] = gurobipy_mock

    highspy_mock = types.ModuleType("highspy")
    highspy_mock.Highs = type("Highs", (), {})
    sys.modules["highspy"] = highspy_mock

    pulp_mock = types.ModuleType("pulp")
    pulp_mock.LpProblem = type("LpProblem", (), {})
    sys.modules["pulp"] = pulp_mock

    swiglpk_mock = types.ModuleType("swiglpk")
    sys.modules["swiglpk"] = swiglpk_mock

    pyscipopt_mock = types.ModuleType("pyscipopt")
    pyscipopt_mock.Model = type("Model", (), {})
    sys.modules["pyscipopt"] = pyscipopt_mock

    ecos_mock = types.ModuleType("ecos")
    sys.modules["ecos"] = ecos_mock

    osqp_mock = types.ModuleType("osqp")
    sys.modules["osqp"] = osqp_mock

    cvxopt_mock = types.ModuleType("cvxopt")
    sys.modules["cvxopt"] = cvxopt_mock

    scs_mock = types.ModuleType("scs")
    sys.modules["scs"] = scs_mock
