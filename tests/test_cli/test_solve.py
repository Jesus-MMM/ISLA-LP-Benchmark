"""
Tests para el modulo solve (CLI resolver).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Prevent circular import by pre-patching visualization
import unittest.mock as mock
sys.modules['src.visualization'] = mock.MagicMock()
sys.modules['src.visualization.LinearVisualization'] = mock.MagicMock()

from pathlib import Path  # noqa: E402
from unittest.mock import patch, MagicMock  # noqa: E402


class TestSolveSingle:
    """Tests para solve_single."""

    def test_file_not_found(self):
        from src.cli.solve import solve_single
        rc = solve_single(Path("no_existe.lp"))
        assert rc == 1

    def test_solver_not_found(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = None
                rc = solve_single(Path(tmp))
                assert rc == 1
        finally:
            os.unlink(tmp)

    def test_successful_solve(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 42.0
            mock_solver.solve.return_value.variables = {"x": 42.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                rc = solve_single(Path(tmp))
                assert rc == 0
        finally:
            os.unlink(tmp)

    def test_json_output(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 42.0
            mock_solver.solve.return_value.variables = {"x": 42.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                rc = solve_single(Path(tmp), json_output=True)
                assert rc == 0
        finally:
            os.unlink(tmp)

    def test_json_output_to_file(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            json_path = tmp + ".json"
            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 42.0
            mock_solver.solve.return_value.variables = {"x": 42.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                rc = solve_single(Path(tmp), json_output=True, output=json_path)
                assert rc == 0
                assert os.path.exists(json_path)
                os.unlink(json_path)
        finally:
            os.unlink(tmp)

    def test_solver_raises_typeerror(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            class SolverThatRaisesTypeError:
                def __init__(self, problem, config=None):
                    if config is not None:
                        raise TypeError()
                    self.config = None

                def solve(self):
                    result = MagicMock()
                    result.is_optimal.return_value = True
                    result.objective_value = 1.0
                    result.variables = {"x": 1.0}
                    result.status = "optimal"
                    return result

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = SolverThatRaisesTypeError
                rc = solve_single(Path(tmp))
                assert rc == 0
        finally:
            os.unlink(tmp)

    def test_non_optimal_status(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = False
            mock_solver.solve.return_value.status = "infeasible"

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                with patch("src.cli.solve._console") as mock_console:
                    rc = solve_single(Path(tmp))
                    assert rc == 0
                    found = any("infeasible" in str(c) for c in mock_console.print.call_args_list)
                    assert found
        finally:
            os.unlink(tmp)

    def test_visualize_2d(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 42.0
            mock_solver.solve.return_value.variables = {"x": 10.0, "y": 5.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                with patch("src.cli.solve.LinearVisualization") as mock_viz:
                    mock_viz_instance = MagicMock()
                    mock_viz.return_value = mock_viz_instance
                    rc = solve_single(Path(tmp), visualize=True)
                    assert rc == 0
                    mock_viz_instance.plot.assert_called_once()
        finally:
            os.unlink(tmp)

    def test_times_flag(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 42.0
            mock_solver.solve.return_value.variables = {"x": 42.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                with patch("src.cli.solve._console") as mock_console:
                    rc = solve_single(Path(tmp), times=True)
                    assert rc == 0
                    assert mock_console.print.call_count >= 2
        finally:
            os.unlink(tmp)

    def test_pdf_flag(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 42.0
            mock_solver.solve.return_value.variables = {"x": 10.0, "y": 5.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                with patch("src.cli.solve._render_report") as mock_render:
                    with patch("src.report.adapters.adapt_single_solution") as mock_adapt:
                        mock_adapt.return_value = MagicMock(variables={}, tables={})
                        with patch("src.cli.get_system_info"):
                            rc = solve_single(Path(tmp), report_format="pdf")
                            assert rc == 0
                            mock_render.assert_called_once()
        finally:
            os.unlink(tmp)

    def test_error_handler_verbose(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.side_effect = RuntimeError("unexpected error")
                with patch("src.cli.solve._console") as mock_console:
                    rc = solve_single(Path(tmp), verbose=True)
                    assert rc == 1
                    found = any("Error" in str(c) for c in mock_console.print.call_args_list)
                    assert found
        finally:
            os.unlink(tmp)

    def test_quiet_json_output_to_stdout(self):
        from src.cli.solve import solve_single
        import tempfile
        content = "max: x + y;\n x + y <= 10;\n x >= 0;\n y >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 42.0
            mock_solver.solve.return_value.variables = {"x": 42.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = lambda p, c: mock_solver
                with patch("src.cli.solve._console") as mock_console:
                    rc = solve_single(Path(tmp), json_output=True, quiet=True)
                    assert rc == 0
                    # Should print JSON even in quiet mode
                    assert mock_console.print.call_count >= 1
        finally:
            os.unlink(tmp)


class TestSolveMulti:
    """Tests para solve_multi."""

    def test_file_not_found(self):
        from src.cli.solve import solve_multi
        rc = solve_multi(Path("no_existe.lp"))
        assert rc == 1

    def test_solver_not_found(self):
        from src.cli.solve import solve_multi
        import tempfile
        content = "max: x;\nx >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.return_value = None
                rc = solve_multi(Path(tmp))
                assert rc == 1
        finally:
            os.unlink(tmp)

    def test_solve_multi_basic_success(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            mock_problem = MagicMock()
            mock_problem.variables = ["x"]

            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 1.0
            mock_solver.solve.return_value.variables = {"x": 1.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.parser.MultiLPParser") as mock_mp:
                mock_mp.return_value.parse_all.return_value = [mock_problem, mock_problem]
                with patch("src.cli.solve.SolverRegistry") as mock_reg:
                    mock_reg.get.return_value = lambda p, c: mock_solver
                    rc = solve_multi(Path(tmp))
                    assert rc == 0
        finally:
            os.unlink(tmp)

    def test_solve_multi_json_output(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            mock_problem = MagicMock()
            mock_problem.variables = ["x"]

            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 1.0
            mock_solver.solve.return_value.variables = {"x": 1.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.parser.MultiLPParser") as mock_mp:
                mock_mp.return_value.parse_all.return_value = [mock_problem]
                with patch("src.cli.solve.SolverRegistry") as mock_reg:
                    mock_reg.get.return_value = lambda p, c: mock_solver
                    with patch("src.cli.solve._console") as mock_console:
                        rc = solve_multi(Path(tmp), json_output=True)
                        assert rc == 0
                        assert mock_console.print.call_count >= 1
        finally:
            os.unlink(tmp)

    def test_solve_multi_visualize(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            mock_problem = MagicMock()
            mock_problem.variables = ["x", "y"]

            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 1.0
            mock_solver.solve.return_value.variables = {"x": 1.0, "y": 0.5}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.parser.MultiLPParser") as mock_mp:
                mock_mp.return_value.parse_all.return_value = [mock_problem]
                with patch("src.cli.solve.SolverRegistry") as mock_reg:
                    mock_reg.get.return_value = lambda p, c: mock_solver
                with patch("src.visualization.LinearVisualization", return_value=MagicMock()) as mock_viz:
                    mock_viz.return_value.plot.return_value = None
                    rc = solve_multi(Path(tmp), visualize=True)
                    assert rc == 0
                    mock_viz.return_value.plot.assert_called_once()
        finally:
            os.unlink(tmp)

    def test_solve_multi_pdf(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            mock_problem = MagicMock()
            mock_problem.variables = ["x"]

            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 1.0
            mock_solver.solve.return_value.variables = {"x": 1.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.parser.MultiLPParser") as mock_mp:
                mock_mp.return_value.parse_all.return_value = [mock_problem]
                with patch("src.cli.solve.SolverRegistry") as mock_reg:
                    mock_reg.get.return_value = lambda p, c: mock_solver
                    with patch("src.cli.solve._render_report") as mock_render:
                        with patch("src.cli.get_system_info"):
                            rc = solve_multi(Path(tmp), report_format="pdf")
                            assert rc == 0
                            mock_render.assert_called_once()
        finally:
            os.unlink(tmp)

    def test_solve_multi_problem_solve_error(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            mock_problem = MagicMock()
            mock_problem.variables = ["x"]

            def failing_solver(problem, config):
                raise RuntimeError("solver failed")

            with patch("src.parser.MultiLPParser") as mock_mp:
                mock_mp.return_value.parse_all.return_value = [mock_problem]
                with patch("src.cli.solve.SolverRegistry") as mock_reg:
                    mock_reg.get.return_value = failing_solver
                    rc = solve_multi(Path(tmp))
                    assert rc == 0
        finally:
            os.unlink(tmp)

    def test_solve_multi_top_level_error(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.side_effect = RuntimeError("top error")
                with patch("src.cli.solve._console"):
                    rc = solve_multi(Path(tmp))
                    assert rc == 1
        finally:
            os.unlink(tmp)

    def test_solve_multi_non_optimal(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            mock_problem = MagicMock()
            mock_problem.variables = ["x"]

            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = False
            mock_solver.solve.return_value.status = "infeasible"

            with patch("src.parser.MultiLPParser") as mock_mp:
                mock_mp.return_value.parse_all.return_value = [mock_problem]
                with patch("src.cli.solve.SolverRegistry") as mock_reg:
                    mock_reg.get.return_value = lambda p, c: mock_solver
                    with patch("src.cli.solve._console") as mock_console:
                        rc = solve_multi(Path(tmp))
                        assert rc == 0
                        found = any("infeasible" in str(c) for c in mock_console.print.call_args_list)
                        assert found
        finally:
            os.unlink(tmp)

    def test_solve_multi_pdf_error(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            mock_problem = MagicMock()
            mock_problem.variables = ["x"]

            mock_solver = MagicMock()
            mock_solver.solve.return_value.is_optimal.return_value = True
            mock_solver.solve.return_value.objective_value = 1.0
            mock_solver.solve.return_value.variables = {"x": 1.0}
            mock_solver.solve.return_value.status = "optimal"

            with patch("src.parser.MultiLPParser") as mock_mp:
                mock_mp.return_value.parse_all.return_value = [mock_problem]
                with patch("src.cli.solve.SolverRegistry") as mock_reg:
                    mock_reg.get.return_value = lambda p, c: mock_solver
                    with patch("src.cli.solve._render_report") as mock_render:
                        mock_render.side_effect = RuntimeError("report failed")
                        with patch("src.cli.solve._console"):
                            rc = solve_multi(Path(tmp), report_format="pdf", verbose=True)
                            assert rc == 0
        finally:
            os.unlink(tmp)

    def test_solve_multi_verbose_top_error(self):
        from src.cli.solve import solve_multi
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write("placeholder")
            tmp = f.name
        try:
            with patch("src.cli.solve.SolverRegistry") as mock_reg:
                mock_reg.get.side_effect = RuntimeError("verbose error")
                with patch("src.cli.solve._console"):
                    rc = solve_multi(Path(tmp), verbose=True)
                    assert rc == 1
        finally:
            os.unlink(tmp)
