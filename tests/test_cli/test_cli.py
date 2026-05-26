"""
Tests para el CLI argument parser y funciones auxiliares.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cli.__main__ import create_parser, _version


class TestCreateParser:
    """Tests para create_parser."""

    def test_default_parser(self):
        """Test parser con argumentos por defecto."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.input is None
        assert args.solver == "gurobi"
        assert args.verbose is False
        assert args.quiet is False
        assert args.json is False
        assert args.multi is False

    def test_input_positional(self):
        """Test argumento posicional input."""
        parser = create_parser()
        args = parser.parse_args(["problema.txt"])
        assert args.input == "problema.txt"

    def test_solver_flag(self):
        """Test flag --solver / -s."""
        parser = create_parser()
        args = parser.parse_args(["-s", "highs"])
        assert args.solver == "highs"

    def test_verbose_flag(self):
        """Test flag --verbose."""
        parser = create_parser()
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

    def test_quiet_flag(self):
        """Test flag --quiet / -q."""
        parser = create_parser()
        args = parser.parse_args(["-q"])
        assert args.quiet is True

    def test_json_flag(self):
        """Test flag --json / -j."""
        parser = create_parser()
        args = parser.parse_args(["-j"])
        assert args.json is True

    def test_multi_flag(self):
        """Test flag --multi / -m."""
        parser = create_parser()
        args = parser.parse_args(["-m"])
        assert args.multi is True

    def test_visualize_flag(self):
        """Test flag --visualize / -v."""
        parser = create_parser()
        args = parser.parse_args(["-v"])
        assert args.visualize is True

    def test_pdf_flag(self):
        """Test flag --pdf / -p."""
        parser = create_parser()
        args = parser.parse_args(["-p"])
        assert args.pdf is True

    def test_times_flag(self):
        """Test flag --times / -t."""
        parser = create_parser()
        args = parser.parse_args(["-t"])
        assert args.times is True

    def test_no_solve_flag(self):
        """Test flag --no-solve / -n."""
        parser = create_parser()
        args = parser.parse_args(["-n"])
        assert args.no_solve is True

    def test_benchmark_flag(self):
        """Test flag --benchmark / -b."""
        parser = create_parser()
        args = parser.parse_args(["-b"])
        assert args.benchmark is True

    def test_output_flag(self):
        """Test flag --output / -o."""
        parser = create_parser()
        args = parser.parse_args(["-o", "salida.json"])
        assert args.output == "salida.json"

    def test_timeout_flag(self):
        """Test flag --timeout / -T."""
        parser = create_parser()
        args = parser.parse_args(["-T", "30"])
        assert args.timeout == 30.0

    def test_solvers_list_flag(self):
        """Test flag --solvers / -S."""
        parser = create_parser()
        args = parser.parse_args(["-S", "highs", "cbc", "glpk"])
        assert args.solvers == ["highs", "cbc", "glpk"]

    def test_all_solvers_flag(self):
        """Test flag --all-solvers / -a."""
        parser = create_parser()
        args = parser.parse_args(["-a"])
        assert args.all_solvers is True

    def test_repetitions_flag(self):
        """Test flag --repetitions / -r."""
        parser = create_parser()
        args = parser.parse_args(["-r", "5"])
        assert args.repetitions == 5

    def test_log_level(self):
        """Test --log-level flag."""
        parser = create_parser()
        args = parser.parse_args(["--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_list_solvers(self):
        """Test --list-solvers / -l."""
        parser = create_parser()
        args = parser.parse_args(["-l"])
        assert args.list_solvers is True

    def test_output_dir(self):
        """Test --output-dir / -O."""
        parser = create_parser()
        args = parser.parse_args(["-O", "results/"])
        assert args.output_dir == "results/"

    def test_output_csv(self):
        """Test --output-csv."""
        parser = create_parser()
        args = parser.parse_args(["--output-csv", "benchmark.csv"])
        assert args.output_csv == "benchmark.csv"

    def test_plot_comparison(self):
        """Test --plot-comparison / -C."""
        parser = create_parser()
        args = parser.parse_args(["-C"])
        assert args.plot_comparison is True

    def test_combined_flags(self):
        """Test combinacion de flags."""
        parser = create_parser()
        args = parser.parse_args([
            "input.lp", "-s", "highs", "-v", "-p", "-t", "-j", "-q",
        ])
        assert args.input == "input.lp"
        assert args.solver == "highs"
        assert args.visualize is True
        assert args.pdf is True
        assert args.times is True
        assert args.json is True
        assert args.quiet is True


class TestVersion:
    """Tests para _version."""

    def test_version_returns_string(self):
        """Test _version retorna un string."""
        version = _version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_version_format(self):
        """Test formato de version X.Y.Z."""
        version = _version()
        parts = version.split(".")
        assert len(parts) >= 2


class TestParserHelp:
    """Tests para el texto de ayuda."""

    def test_help_generated(self):
        """Test que el help se genera sin errores."""
        parser = create_parser()
        help_text = parser.format_help()
        assert len(help_text) > 0
        assert "lp-solver" in help_text

    def test_help_contains_key_sections(self):
        """Test que el help contiene secciones importantes."""
        parser = create_parser()
        help_text = parser.format_help()
        assert "Informacion" in help_text
        assert "Seleccion de solver" in help_text
        assert "Opciones de resolucion" in help_text
        assert "Opciones de benchmark" in help_text
        assert "Opciones de salida" in help_text

    def test_usage_in_help(self):
        """Test que el help contiene usage."""
        parser = create_parser()
        help_text = parser.format_help()
        assert "usage:" in help_text.lower()

    def test_default_solver_in_help(self):
        """Test que el solver por defecto aparece en help."""
        parser = create_parser()
        help_text = parser.format_help()
        assert "gurobi" in help_text

    def test_epilog_examples(self):
        """Test que los ejemplos aparecen en el epilog."""
        parser = create_parser()
        help_text = parser.format_help()
        assert "Ejemplos" in help_text
