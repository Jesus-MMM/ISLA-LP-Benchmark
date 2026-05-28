"""
Tests para BaseSolver y SolverRegistry.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.problem import LinearProblem
from src.core.solution import Solution
from src.solver.base import BaseSolver, SolverRegistry, SolverStats


class _ConcreteSolver(BaseSolver):
    """Solver concreto para testing (implementa solve)."""
    def solve(self) -> Solution:
        return Solution(status="OPTIMAL", objective_value=0.0, variables={})


class TestSolverRegistry:
    """Tests para SolverRegistry."""

    def setup_method(self):
        """Limpia el registro antes de cada test."""
        self._original_solvers = dict(SolverRegistry._solvers)
        self._original_availability = dict(SolverRegistry._availability)
        self._original_errors = dict(SolverRegistry._errors)

    def teardown_method(self):
        """Restaura el estado original del registro."""
        SolverRegistry._solvers = self._original_solvers
        SolverRegistry._availability = self._original_availability
        SolverRegistry._errors = self._original_errors

    def test_register(self):
        """Test registrar un solver."""
        SolverRegistry.register("test_solver", _ConcreteSolver)
        assert SolverRegistry.get("test_solver") is _ConcreteSolver

    def test_register_lowercase(self):
        """Test que el nombre se almacena en minusculas."""
        SolverRegistry.register("MixedCase", _ConcreteSolver)
        assert SolverRegistry.get("mixedcase") is _ConcreteSolver

    def test_get_nonexistent(self):
        """Test get con solver no registrado."""
        assert SolverRegistry.get("nonexistent") is None

    def test_list_solvers(self):
        """Test list_solvers."""
        SolverRegistry.register("solver_a", _ConcreteSolver)
        SolverRegistry.register("solver_b", _ConcreteSolver)
        solvers = SolverRegistry.list_solvers()
        assert "solver_a" in solvers
        assert "solver_b" in solvers

    def test_list_solvers_available_only(self):
        """Test list_solvers con available_only=True."""
        SolverRegistry.register("available_solver", _ConcreteSolver, available=True)
        SolverRegistry.register("unavailable_solver", _ConcreteSolver, available=False)
        available = SolverRegistry.list_solvers(available_only=True)
        assert "available_solver" in available
        assert "unavailable_solver" not in available

    def test_list_all_info(self):
        """Test list_all_info."""
        SolverRegistry.register("info_test", _ConcreteSolver, available=True)
        info = SolverRegistry.list_all_info()
        assert "info_test" in info
        assert info["info_test"]["available"] is True

    def test_set_unavailable(self):
        """Test set_unavailable."""
        SolverRegistry.register("solver", _ConcreteSolver, available=True)
        SolverRegistry.set_unavailable("solver", "no disponible")
        assert not SolverRegistry.is_available("solver")
        assert SolverRegistry.get_error("solver") == "no disponible"

    def test_is_available(self):
        """Test is_available."""
        SolverRegistry.register("s", _ConcreteSolver, available=True)
        SolverRegistry.register("t", _ConcreteSolver, available=False)
        assert SolverRegistry.is_available("s")
        assert not SolverRegistry.is_available("t")

    def test_get_error(self):
        """Test get_error."""
        SolverRegistry.register("err_solver", _ConcreteSolver)
        SolverRegistry.set_unavailable("err_solver", "error message")
        assert SolverRegistry.get_error("err_solver") == "error message"

    def test_get_error_empty(self):
        """Test get_error sin error."""
        SolverRegistry.register("clean_solver", _ConcreteSolver)
        assert SolverRegistry.get_error("clean_solver") == ""

    def test_create_solver(self):
        """Test create_solver returns instance."""
        SolverRegistry.register("creatable", _ConcreteSolver)
        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        instance = SolverRegistry.create_solver("creatable", problem=problem)
        assert isinstance(instance, BaseSolver)

    def test_create_solver_nonexistent(self):
        """Test create_solver with nonexistent solver."""
        assert SolverRegistry.create_solver("ghost") is None


class TestBaseSolver:
    """Tests para BaseSolver."""

    def _make_problem(self):
        return LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )

    def test_initialization(self):
        """Test inicializacion basica."""
        problem = self._make_problem()
        solver = _ConcreteSolver(problem)
        assert solver.problem is problem
        assert solver.config.verbose is False

    def test_custom_config(self):
        """Test configuracion personalizada."""
        problem = self._make_problem()
        config = BaseSolver.Config(verbose=True, time_limit=30.0)
        solver = _ConcreteSolver(problem, config)
        assert solver.config.verbose is True
        assert solver.config.time_limit == 30.0

    def test_solver_name(self):
        """Test solver_name property."""
        solver = _ConcreteSolver(self._make_problem())
        assert solver.solver_name == "BaseSolver"

    def test_solver_version(self):
        """Test solver_version property."""
        solver = _ConcreteSolver(self._make_problem())
        assert solver.solver_version == "0.0.0"

    def test_is_available(self):
        """Test is_available property."""
        solver = _ConcreteSolver(self._make_problem())
        assert solver.is_available is True

    def test_get_stats(self):
        """Test get_stats returns SolverStats."""
        solver = _ConcreteSolver(self._make_problem())
        stats = solver.get_stats()
        assert isinstance(stats, SolverStats)
        assert stats.solve_time == 0.0

    def test_reset_stats(self):
        """Test reset restablece estadisticas."""
        solver = _ConcreteSolver(self._make_problem())
        solver.stats.solve_time = 10.0
        solver.reset()
        assert solver.stats.solve_time == 0.0

    def test_default_config_values(self):
        """Test valores por defecto de Config."""
        config = BaseSolver.Config()
        assert config.verbose is False
        assert config.time_limit is None
        assert config.mip_gap is None
        assert config.threads is None
        assert config.presolve == 1
        assert config.seed is None

    def test_solver_capabilities_default(self):
        """Test capacidades por defecto."""
        solver = _ConcreteSolver(self._make_problem())
        assert solver.capabilities.lp is True
        assert solver.capabilities.milp is True
        assert solver.capabilities.qp is False

    def test_solve_returns_solution(self):
        """Test solve concreto retorna Solution."""
        solver = _ConcreteSolver(self._make_problem())
        solution = solver.solve()
        assert isinstance(solution, Solution)
        assert solution.status == "OPTIMAL"

    def test_repr(self):
        """Test __repr__."""
        solver = _ConcreteSolver(self._make_problem())
        r = repr(solver)
        assert "BaseSolver" in r
        assert "available" in r


class TestSolverStats:
    """Tests para SolverStats."""

    def test_defaults(self):
        """Test valores por defecto."""
        stats = SolverStats()
        assert stats.solve_time == 0.0
        assert stats.build_time == 0.0
        assert stats.iterations == 0
        assert stats.nodes == 0
        assert stats.memory_used_mb == 0.0

    def test_set_values(self):
        """Test asignacion de valores."""
        stats = SolverStats()
        stats.solve_time = 1.5
        stats.iterations = 100
        stats.nodes = 10
        assert stats.solve_time == 1.5
        assert stats.iterations == 100
        assert stats.nodes == 10
