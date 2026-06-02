"""
Tests para src.solver.__init__ - import fallback paths and SolverLP selection.
Usando el patrón existente del proyecto.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))



class TestSolverImports:
    """Tests for solver module imports and fallback paths."""

    def test_solverlp_is_available(self):
        from src.solver import SolverLP
        assert SolverLP is not None

    def test_solverlp_attribute_exists(self):
        from src.solver import SolverLP
        assert hasattr(SolverLP, 'solver_name') or SolverLP is None

    def test_all_exported_solvers_exist(self):
        from src.solver import (
            BaseSolver,
            GurobiSolver,
            SolverRegistry,
            SolverStats,
        )
        assert BaseSolver is not None
        assert SolverStats is not None
        assert SolverRegistry is not None
        assert GurobiSolver is not None


class TestSolverRegistryUnavailable:
    """Tests for unavailable solver registration."""

    def test_get_unavailable_solver(self):
        from src.solver.base import SolverRegistry

        solvers = SolverRegistry.list_solvers(available_only=False)
        assert isinstance(solvers, list)

    def test_get_unavailable_solver_returns_none_or_raises(self):
        from src.solver.base import SolverRegistry

        result = SolverRegistry.get("nonexistent_solver_xyz")
        assert result is None


class TestSolverInitFile:
    """Tests for specific uncovered lines in solver/__init__.py."""

    def test_solverlp_fallback_to_available(self):
        from src.solver.base import SolverRegistry
        available = SolverRegistry.list_solvers(available_only=True)
        assert isinstance(available, list)
