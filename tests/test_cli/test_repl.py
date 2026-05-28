"""
Tests para el modulo REPL.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import patch, MagicMock


class TestREPL:
    """Tests para funciones del REPL."""

    def test_cmd_info_no_problem(self):
        """Test info sin problema cargado."""
        from src.cli.repl import _cmd_info
        with patch("src.cli.repl._console") as mock_console:
            _cmd_info(None)
            mock_console.print.assert_called_once()

    def test_cmd_info_with_problem(self):
        """Test info con problema cargado."""
        from src.cli.repl import _cmd_info
        from src.core import LinearProblem, LinearConstraint

        problem = LinearProblem(
            objective={"x": 1, "y": 2},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=", name="R1")],
            variables=["x", "y"],
            bounds={},
        )
        with patch("src.cli.repl._console") as mock_console:
            _cmd_info(problem)
            assert mock_console.print.call_count >= 2

    def test_cmd_solve_no_problem(self):
        """Test solve sin problema cargado."""
        from src.cli.repl import _cmd_solve_repl
        with patch("src.cli.repl._console") as mock_console:
            _cmd_solve_repl([], 0, "highs")
            mock_console.print.assert_called_once()

    def test_cmd_solve_with_problem(self):
        """Test solve con problema cargado."""
        from src.cli.repl import _cmd_solve_repl
        from src.core import LinearProblem, LinearConstraint

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=", name="R1")],
            variables=["x"],
            bounds={},
        )
        with patch("src.cli.repl._console") as mock_console:
            with patch("src.cli.repl.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = None
                _cmd_solve_repl([problem], 0, "nonexistent")
                mock_console.print.assert_called_once()

    def test_cmd_solve_optimal(self):
        """Test solve con solucion optima."""
        from src.cli.repl import _cmd_solve_repl
        from src.core import LinearProblem, LinearConstraint

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=", name="R1")],
            variables=["x"],
            bounds={},
        )
        mock_solution = MagicMock()
        mock_solution.is_optimal.return_value = True
        mock_solution.objective_value = 42.0
        mock_solution.variables = {"x": 42.0}
        mock_solver = MagicMock()
        mock_solver.solve.return_value = mock_solution

        with patch("src.cli.repl._console") as mock_console:
            with patch("src.cli.repl.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                _cmd_solve_repl([problem], 0, "highs")
                assert mock_console.print.call_count >= 2

    def test_cmd_solve_exception(self):
        """Test solve con excepcion del solver."""
        from src.cli.repl import _cmd_solve_repl
        from src.core import LinearProblem

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )

        def failing_solver(problem, config):
            raise RuntimeError("solver crashed")

        with patch("src.cli.repl._console"):
            with patch("src.cli.repl.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = failing_solver
                _cmd_solve_repl([problem], 0, "highs")

    def test_cmd_solve_not_optimal(self):
        """Test solve con solucion no optima."""
        from src.cli.repl import _cmd_solve_repl
        from src.core import LinearProblem, LinearConstraint

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[LinearConstraint(coefficients={"x": 1}, rhs=10, sense="<=", name="R1")],
            variables=["x"],
            bounds={},
        )
        mock_solution = MagicMock()
        mock_solution.is_optimal.return_value = False
        mock_solution.status = "infeasible"
        mock_solver = MagicMock()
        mock_solver.solve.return_value = mock_solution

        with patch("src.cli.repl._console") as mock_console:
            with patch("src.cli.repl.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                _cmd_solve_repl([problem], 0, "highs")
                mock_console.print.assert_called()

    def test_cmd_vars_no_problem(self):
        """Test vars sin problema."""
        from src.cli.repl import _cmd_vars
        with patch("src.cli.repl._console") as mock_console:
            _cmd_vars(None)
            mock_console.print.assert_called_once()

    def test_cmd_vars_with_problem(self):
        """Test vars con problema."""
        from src.cli.repl import _cmd_vars
        from src.core import LinearProblem

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x", "y"],
            bounds={},
        )
        with patch("src.cli.repl._console") as mock_console:
            _cmd_vars(problem)
            assert mock_console.print.call_count >= 1

    def test_cmd_export_no_problem(self):
        """Test export sin problema."""
        from src.cli.repl import _cmd_export
        with patch("src.cli.repl._console") as mock_console:
            _cmd_export(None, "out.lp")
            mock_console.print.assert_called_once()

    def test_cmd_export_no_arg(self):
        """Test export sin argumento."""
        from src.cli.repl import _cmd_export
        from src.core import LinearProblem

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        with patch("src.cli.repl._console") as mock_console:
            _cmd_export(problem, "")
            mock_console.print.assert_called_once()

    def test_cmd_export_success(self):
        """Test export exitoso."""
        from src.cli.repl import _cmd_export
        from src.core import LinearProblem
        import tempfile

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False) as f:
            tmp = f.name
        try:
            with patch("src.cli.repl._console") as mock_console:
                _cmd_export(problem, tmp)
                mock_console.print.assert_called()
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def test_cmd_export_error(self):
        """Test export con error."""
        from src.cli.repl import _cmd_export
        from src.core import LinearProblem

        problem = LinearProblem(
            objective={"x": 1},
            sense="max",
            constraints=[],
            variables=["x"],
            bounds={},
        )
        with patch("src.cli.repl._console") as mock_console:
            _cmd_export(problem, "/invalid/path/out.lp")
            mock_console.print.assert_called()

    def test_cmd_load_no_arg(self):
        """Test load sin argumento."""
        from src.cli.repl import _cmd_load
        with patch("src.cli.repl._console"):
            result = _cmd_load("")
            assert result is None

    def test_cmd_load_file_not_found(self):
        """Test load con archivo inexistente."""
        from src.cli.repl import _cmd_load
        with patch("src.cli.repl._console"):
            result = _cmd_load("no_existe.lp")
            assert result is None

    def test_cmd_load_success(self):
        """Test load exitoso."""
        from src.cli.repl import _cmd_load
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            result = _cmd_load(tmp)
            assert result is not None
        finally:
            os.unlink(tmp)

    def test_cmd_load_parse_error(self):
        """Test load con error de parseo."""
        from src.cli.repl import _cmd_load
        import tempfile
        content = "max: x;\nx >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with patch("src.cli.repl.LPParser") as mock_parser:
                mock_parser.return_value.parse.side_effect = ValueError("parse error")
                with patch("src.cli.repl._console"):
                    result = _cmd_load(tmp)
                    assert result is None
        finally:
            os.unlink(tmp)

    def test_cmd_load_mps_no_arg(self):
        """Test load-mps sin argumento."""
        from src.cli.repl import _cmd_load_mps
        with patch("src.cli.repl._console"):
            result = _cmd_load_mps("")
            assert result is None

    def test_cmd_load_mps_file_not_found(self):
        """Test load-mps con archivo inexistente."""
        from src.cli.repl import _cmd_load_mps
        with patch("src.cli.repl._console"):
            result = _cmd_load_mps("no_existe.mps")
            assert result is None

    def test_cmd_load_mps_parse_error(self):
        """Test load-mps con error de parseo."""
        from src.cli.repl import _cmd_load_mps
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mps", delete=False, encoding="utf-8") as f:
            f.write("some content")
            tmp = f.name
        try:
            with patch("src.cli.repl.MPSParser") as mock_parser:
                mock_parser.return_value.parse.side_effect = ValueError("MPS error")
                with patch("src.cli.repl._console"):
                    result = _cmd_load_mps(tmp)
                    assert result is None
        finally:
            os.unlink(tmp)

    def test_cmd_load_mps_success(self):
        """Test load-mps exitoso."""
        from src.cli.repl import _cmd_load_mps
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mps", delete=False, encoding="utf-8") as f:
            f.write("dummy")
            tmp = f.name
        try:
            mock_problem = MagicMock()
            mock_problem.variables = ["x", "y"]
            mock_problem.constraints = []
            mock_problem.sense = "max"
            with patch("src.cli.repl.MPSParser") as mock_parser:
                mock_parser.return_value.parse.return_value = mock_problem
                with patch("src.cli.repl._console"):
                    result = _cmd_load_mps(tmp)
                    assert result is not None
        finally:
            os.unlink(tmp)

    def test_cmd_solvers(self):
        """Test listar solvers."""
        from src.cli.repl import _cmd_solvers
        with patch("src.cli.repl._console"):
            with patch("src.cli.repl.SolverRegistry") as mock_reg:
                mock_reg.list_all_info.return_value = {}
                _cmd_solvers()

    def test_print_help(self):
        """Test print help."""
        from src.cli.repl import _print_help
        with patch("src.cli.repl._console") as mock_console:
            _print_help()
            mock_console.print.assert_called_once()

    def test_run_repl_quit(self):
        """Test run_repl with quit."""
        from src.cli.repl import run_repl
        with patch("src.cli.repl.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = EOFError()
            rc = run_repl()
            assert rc == 0

    def test_run_repl_keyboard_interrupt(self):
        """Test run_repl with Ctrl+C."""
        from src.cli.repl import run_repl
        with patch("src.cli.repl.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = KeyboardInterrupt()
            rc = run_repl()
            assert rc == 0

    def test_run_repl_command_dispatch(self):
        """Test run_repl dispatches all commands correctly."""
        from src.cli.repl import run_repl

        commands = ["", "help", "load", "load-mps", "load-multi", "problems", "select 1", "info", "solve", "benchmark", "solvers", "vars", "export", "unknown_cmd", "quit"]

        with patch("src.cli.repl.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = commands
            with patch("src.cli.repl._cmd_load") as mock_load:
                with patch("src.cli.repl._cmd_load_mps") as mock_load_mps:
                    with patch("src.cli.repl._cmd_load_multi") as mock_load_multi:
                        with patch("src.cli.repl._cmd_problems") as mock_problems:
                            with patch("src.cli.repl._cmd_select") as mock_select:
                                with patch("src.cli.repl._cmd_info") as mock_info:
                                    with patch("src.cli.repl._cmd_solve_repl") as mock_solve:
                                        with patch("src.cli.repl._cmd_benchmark") as mock_benchmark:
                                            with patch("src.cli.repl._cmd_solvers") as mock_solvers:
                                                with patch("src.cli.repl._cmd_vars") as mock_vars:
                                                    with patch("src.cli.repl._cmd_export") as mock_export:
                                                        with patch("src.cli.repl._console") as mock_console:
                                                            # Make load/select return None/empty to keep state clean
                                                            mock_load.return_value = None
                                                            mock_load_mps.return_value = None
                                                            mock_load_multi.return_value = []
                                                            mock_select.return_value = None
                                                            rc = run_repl()
                                                            assert rc == 0
                                                            mock_load.assert_called_once()
                                                            mock_load_mps.assert_called_once()
                                                            mock_load_multi.assert_called_once()
                                                            mock_problems.assert_called_once()
                                                            mock_select.assert_called_once()
                                                            mock_info.assert_called_once()
                                                            mock_solve.assert_called_once()
                                                            mock_benchmark.assert_called_once()
                                                            mock_solvers.assert_called_once()
                                                            mock_vars.assert_called_once()
                                                            mock_export.assert_called_once()
                                                            unknown_calls = [
                                                                c for c in mock_console.print.call_args_list
                                                                if "unknown_cmd" in str(c) or "Comando desconocido" in str(c)
                                                            ]
                                                            assert len(unknown_calls) >= 1
