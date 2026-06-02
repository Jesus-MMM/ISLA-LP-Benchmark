"""
Tests para el modulo CLI principal (__main__).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pathlib import Path  # noqa: E402
from unittest.mock import patch  # noqa: E402

import pytest  # noqa: E402


class TestCreateParser:
    """Tests para create_parser."""

    def _get_parser(self):
        from src.cli.__main__ import create_parser
        return create_parser()

    def test_parser_accepts_input(self):
        parser = self._get_parser()
        args = parser.parse_args(["problema.txt"])
        assert args.input == "problema.txt"

    def test_parser_default_solver(self):
        parser = self._get_parser()
        args = parser.parse_args(["problema.txt"])
        assert args.solver == "gurobi"

    def test_parser_short_solver(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-s", "highs"])
        assert args.solver == "highs"

    def test_parser_benchmark_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["-b", "prob.txt"])
        assert args.benchmark is True

    def test_parser_multi_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-m"])
        assert args.multi is True

    def test_parser_visualize_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-v"])
        assert args.visualize is True

    def test_parser_pdf_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-p"])
        assert args.pdf is True

    def test_parser_times_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-t"])
        assert args.times is True

    def test_parser_no_solve_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-n"])
        assert args.no_solve is True

    def test_parser_json_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-j"])
        assert args.json is True

    def test_parser_quiet_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-q"])
        assert args.quiet is True

    def test_parser_verbose_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "--verbose"])
        assert args.verbose is True

    def test_parser_repl_flag(self):
        parser = self._get_parser()
        args = parser.parse_args(["--repl"])
        assert args.repl is True

    def test_parser_install_completion(self):
        parser = self._get_parser()
        args = parser.parse_args(["--install-completion"])
        assert args.install_completion is True

    def test_parser_list_solvers(self):
        parser = self._get_parser()
        args = parser.parse_args(["-l"])
        assert args.list_solvers is True

    def test_parser_timeout(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-T", "30"])
        assert args.timeout == 30.0

    def test_parser_solvers_list(self):
        parser = self._get_parser()
        args = parser.parse_args(["-b", "prob.txt", "-S", "gurobi", "highs"])
        assert args.solvers == ["gurobi", "highs"]

    def test_parser_repetitions(self):
        parser = self._get_parser()
        args = parser.parse_args(["-b", "prob.txt", "-r", "5"])
        assert args.repetitions == 5

    def test_parser_output(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "-o", "salida.json"])
        assert args.output == "salida.json"

    def test_parser_output_dir(self):
        parser = self._get_parser()
        args = parser.parse_args(["-b", "prob.txt", "-O", "results"])
        assert args.output_dir == "results"

    def test_parser_log_level(self):
        parser = self._get_parser()
        args = parser.parse_args(["prob.txt", "--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_parser_all_solvers(self):
        parser = self._get_parser()
        args = parser.parse_args(["-b", "prob.txt", "-a"])
        assert args.all_solvers is True

    def test_no_input_shows_help(self):
        parser = self._get_parser()
        args = parser.parse_args([])
        assert args.input is None


class TestVersion:
    """Tests para _version."""

    def test_version_returns_string(self):
        from src.cli.__main__ import _version
        v = _version()
        assert isinstance(v, str)
        assert len(v) > 0


class TestMain:
    """Tests para main()."""

    def test_main_version(self):
        from src.cli.__main__ import main
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0

    def test_main_list_solvers(self):
        from src.cli.__main__ import main
        with patch("src.cli.__main__._console"):
            with patch("src.solver.SolverRegistry") as mock_reg:
                mock_reg.list_all_info.return_value = {}
                mock_reg.list_solvers.return_value = []
                rc = main(["--list-solvers"])
                assert rc == 0

    def test_main_list_solvers_mixed(self):
        from src.cli.__main__ import main
        with patch("src.cli.__main__._console") as mock_console:
            with patch("src.solver.SolverRegistry") as mock_reg:
                mock_reg.list_all_info.return_value = {
                    "gurobi": {"available": True, "error": ""},
                    "highs": {"available": False, "error": "not installed"},
                }
                mock_reg.list_solvers.return_value = ["gurobi"]
                rc = main(["--list-solvers"])
                assert rc == 0
                assert mock_console.print.call_count >= 1

    def test_main_install_completion(self):
        from src.cli.__main__ import main
        with patch("src.cli.__main__._console"):
            with patch("src.cli.__main__.Path") as mock_path:
                mock_path.return_value.expanduser.return_value.parent.mkdir.return_value = None
                rc = main(["--install-completion"])
                assert rc == 0

    def test_main_repl(self):
        from src.cli.__main__ import main
        with patch("src.cli.repl.run_repl", return_value=0):
            rc = main(["--repl"])
            assert rc == 0

    def test_main_no_input(self):
        from src.cli.__main__ import main
        rc = main([])
        assert rc == 0

    def test_main_benchmark(self):
        from src.cli.__main__ import main
        with patch("src.cli.benchmark.run_benchmark", return_value=0):
            with patch("src.solver.SolverRegistry"):
                rc = main(["-b", "prob.txt"])
                assert rc == 0

    def test_main_benchmark_all_solvers(self):
        from src.cli.__main__ import main
        with patch("src.cli.benchmark.run_benchmark", return_value=0):
            with patch("src.solver.SolverRegistry") as mock_reg:
                mock_reg.list_solvers.return_value = ["gurobi", "highs"]
                rc = main(["-b", "prob.txt", "-a"])
                assert rc == 0

    def test_main_solve_no_solve(self):
        from src.cli.__main__ import main
        with patch("src.cli.__main__._parse_only", return_value=0):
            rc = main(["prob.txt", "-n"])
            assert rc == 0

    def test_main_solve_single(self):
        from src.cli.__main__ import main
        with patch("src.cli.solve.solve_single", return_value=0):
            rc = main(["prob.txt"])
            assert rc == 0

    def test_main_solve_multi(self):
        from src.cli.__main__ import main
        with patch("src.cli.solve.solve_multi", return_value=0):
            rc = main(["prob.txt", "-m"])
            assert rc == 0

    def test_main_log_level(self):
        from src.cli.__main__ import main
        with patch("src.utils.logging.set_default_level") as mock_set:
            with patch("src.cli.solve.solve_single", return_value=0):
                rc = main(["prob.txt", "--log-level", "DEBUG"])
                assert rc == 0
                mock_set.assert_called_once()


class TestParseOnly:
    """Tests para _parse_only."""

    def test_parse_only_file_not_found(self):
        from src.cli.__main__ import _parse_only
        rc = _parse_only(Path("archivo_inexistente.lp"))
        assert rc == 1

    def test_parse_only_success(self):
        import tempfile

        from src.cli.__main__ import _parse_only
        lp_text = "max: x + y;\nx + y <= 10;\nx >= 0;\ny >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(lp_text)
            tmp_path = f.name
        try:
            rc = _parse_only(Path(tmp_path))
            assert rc == 0
        finally:
            os.unlink(tmp_path)

    def test_parse_only_multi(self):
        import tempfile

        from src.cli.__main__ import _parse_only
        content = "max: x\nx + y <= 10\nx >= 0\ny >= 0\n---\nmax: y\nx + y <= 10\nx >= 0\ny >= 0"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            rc = _parse_only(Path(tmp))
            assert rc == 0
        finally:
            os.unlink(tmp)

    def test_parse_only_error_verbose(self):
        import tempfile

        from src.cli.__main__ import _parse_only
        content = "max: x;\nx >= 0;"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lp", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            with patch("src.parser.LPParser") as mock_lp:
                mock_lp.return_value.parse.side_effect = ValueError("parse error")
                rc = _parse_only(Path(tmp), verbose=True)
                assert rc == 1
        finally:
            os.unlink(tmp)
