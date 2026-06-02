"""
Tests para el modulo de estadisticas (Friedman, Nemenyi, ANOVA).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np


class TestFriedman:
    def test_friedman_basic(self):
        from src.analysis.statistics import friedman_test
        results = np.array([
            [1.0, 2.0, 3.0],
            [1.5, 2.5, 3.5],
            [2.0, 1.0, 3.0],
        ])
        out = friedman_test(results)
        assert "statistic" in out
        assert "p_value" in out
        assert "df" in out
        assert "avg_ranks" in out
        assert out["df"] == 2
        assert len(out["avg_ranks"]) == 3

    def test_friedman_identical(self):
        from src.analysis.statistics import friedman_test
        results = np.array([
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
        ])
        out = friedman_test(results)
        assert out["statistic"] > 0  # Identical rankings still produce positive Q when values differ across rows


class TestNemenyi:
    def test_nemenyi_basic(self):
        from src.analysis.statistics import nemenyi_posthoc
        avg_ranks = np.array([1.5, 2.5, 3.0])
        out = nemenyi_posthoc(avg_ranks, n_problems=10)
        assert "critical_difference" in out
        assert "matrix" in out
        assert "solver_labels" in out
        assert len(out["matrix"]) == 3

    def test_nemenyi_small_k(self):
        from src.analysis.statistics import nemenyi_posthoc
        avg_ranks = np.array([1.0, 2.0])
        out = nemenyi_posthoc(avg_ranks, n_problems=5)
        assert out["critical_difference"] > 0

    def test_nemenyi_large_k(self):
        from src.analysis.statistics import nemenyi_posthoc
        avg_ranks = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        out = nemenyi_posthoc(avg_ranks, n_problems=20)
        assert out["critical_difference"] > 0


class TestANOVA:
    def test_anova_basic(self):
        from src.analysis.statistics import anova_one_way
        groups = [
            np.array([1.0, 2.0, 3.0]),
            np.array([4.0, 5.0, 6.0]),
        ]
        out = anova_one_way(groups)
        assert "statistic" in out
        assert "p_value" in out
        assert "df_between" in out
        assert "df_within" in out

    def test_anova_identical(self):
        from src.analysis.statistics import anova_one_way
        groups = [
            np.array([1.0, 1.0, 1.0]),
            np.array([1.0, 1.0, 1.0]),
        ]
        out = anova_one_way(groups)
        assert np.isnan(out["statistic"])  # All identical values produce NaN F-statistic
