import sys
import types
from unittest.mock import MagicMock


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
