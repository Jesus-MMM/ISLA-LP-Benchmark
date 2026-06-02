"""
Tests para el generador de problemas sinteticos.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.problem_generator import ProblemGenerator


class TestProblemGenerator:
    """Tests para ProblemGenerator."""

    def test_generate_lp_defaults(self):
        """Test generate_lp con valores por defecto."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_lp()
        assert len(problem.variables) == 5
        assert len(problem.constraints) == 10
        assert problem.sense == "max"
        for var in problem.variables:
            assert var in problem.bounds

    def test_generate_lp_custom(self):
        """Test generate_lp con parametros personalizados."""
        gen = ProblemGenerator(random_state=123)
        problem = gen.generate_lp(
            n_vars=10,
            n_constraints=5,
            density=0.5,
            coeff_range=(-1.0, 1.0),
            sense="min",
        )
        assert len(problem.variables) == 10
        assert len(problem.constraints) == 5
        assert problem.sense == "min"

    def test_generate_lp_reproducible(self):
        """Test que misma semilla produce mismo problema."""
        gen1 = ProblemGenerator(random_state=42)
        gen2 = ProblemGenerator(random_state=42)
        p1 = gen1.generate_lp()
        p2 = gen2.generate_lp()
        assert p1.objective == p2.objective
        assert len(p1.constraints) == len(p2.constraints)
        for c1, c2 in zip(p1.constraints, p2.constraints):
            assert c1.coefficients == c2.coefficients
            assert c1.rhs == c2.rhs

    def test_generate_lp_different_seeds(self):
        """Test que semillas diferentes producen problemas diferentes."""
        gen1 = ProblemGenerator(random_state=1)
        gen2 = ProblemGenerator(random_state=2)
        p1 = gen1.generate_lp()
        p2 = gen2.generate_lp()
        assert p1.objective != p2.objective

    def test_generate_lp_empty_objective_fallback(self):
        """Test fallback cuando todos los coeficientes son 0."""
        gen = ProblemGenerator(random_state=0)
        problem = gen.generate_lp(n_vars=1, density=0.0)
        assert len(problem.objective) >= 1

    def test_generate_milp(self):
        """Test generate_milp."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_milp(
            n_vars=5,
            n_constraints=3,
            n_int_vars=2,
        )
        int_count = sum(
            1 for v in problem.variable_types.values() if v == "integer"
        )
        assert int_count == 2

    def test_generate_milp_no_int_vars(self):
        """Test MILP con 0 vars enteras (todas continuas)."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_milp(
            n_vars=5,
            n_constraints=3,
            n_int_vars=0,
        )
        assert all(v == "continuous" for v in problem.variable_types.values())

    def test_generate_netlib_like_afiro(self):
        """Test generate_netlib_like con afiro."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_netlib_like("afiro")
        assert len(problem.variables) == 32
        assert len(problem.constraints) == 27

    def test_generate_netlib_like_unknown(self):
        """Test generate_netlib_like con nombre desconocido."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_netlib_like("unknown")
        assert len(problem.variables) == 50
        assert len(problem.constraints) == 50

    def test_generate_netlib_like_kb2(self):
        """Test generate_netlib_like con kb2."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_netlib_like("kb2")
        assert len(problem.variables) == 41
        assert len(problem.constraints) == 43

    def test_generate_netlib_like_sc50a(self):
        """Test generate_netlib_like con sc50a."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_netlib_like("sc50a")
        assert len(problem.variables) == 50
        assert len(problem.constraints) == 48

    def test_generate_netlib_like_sc50b(self):
        """Test generate_netlib_like con sc50b."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_netlib_like("sc50b")
        assert len(problem.variables) == 50
        assert len(problem.constraints) == 48

    def test_generate_netlib_like_adlittle(self):
        """Test generate_netlib_like con adlittle."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_netlib_like("adlittle")
        assert len(problem.variables) == 97
        assert len(problem.constraints) == 56

    def test_generate_ill_conditioned(self):
        """Test generate_ill_conditioned."""
        gen = ProblemGenerator(random_state=42)
        problem = gen.generate_ill_conditioned()
        assert len(problem.variables) == 10
        assert len(problem.constraints) == 10
        assert problem.sense == "max"
        for c in problem.constraints:
            assert c.sense == "<="
