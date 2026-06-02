"""
Pruebas estadisticas para comparacion de solvers.
Implementa Friedman, Nemenyi post-hoc y ANOVA de una via.
"""


import numpy as np
from scipy.stats import chi2, f_oneway

_Q_ALPHA_005 = {
    2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728,
    6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102,
    10: 3.164, 11: 3.219, 12: 3.268,
}


def friedman_test(results: np.ndarray) -> dict[str, float]:
    """Test de Friedman para comparar k solvers en n problemas.

    Args:
        results: Matriz (n_problemas, n_solvers) con la metrica de rendimiento
                 (ej. tiempo de ejecucion, valor objetivo).

    Returns:
        Dict con 'statistic' (Q de Friedman), 'p_value', 'df',
        'avg_ranks' (rango promedio por solver).
    """
    n, k = results.shape
    ranks = np.apply_along_axis(lambda row: np.argsort(np.argsort(row)) + 1, 1, results)
    avg_ranks = np.mean(ranks, axis=0)

    q = (12.0 * n) / (k * (k + 1.0)) * (
        np.sum(avg_ranks ** 2) - (k * (k + 1.0) ** 2) / 4.0
    )

    p_value = 1.0 - chi2.cdf(q, k - 1)

    return {
        "statistic": float(q),
        "p_value": float(p_value),
        "df": int(k - 1),
        "avg_ranks": avg_ranks.tolist(),
    }


def nemenyi_posthoc(
    avg_ranks: np.ndarray,
    n_problems: int,
    alpha: float = 0.05,
) -> np.ndarray:
    """Test post-hoc de Nemenyi para diferencias criticas entre pares de solvers.

    Args:
        avg_ranks: Rango promedio por solver (del test de Friedman).
        n_problems: Numero de problemas evaluados.
        alpha: Nivel de significancia (default 0.05).

    Returns:
        Matriz (k, k) con diferencias absolutas de rangos.
        Valores que exceden 'critical_difference' son significativos.
    """
    k = len(avg_ranks)
    q_alpha = _Q_ALPHA_005.get(k, 2.343)
    cd = q_alpha * np.sqrt(k * (k + 1.0) / (6.0 * n_problems))

    matrix = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            matrix[i, j] = abs(avg_ranks[i] - avg_ranks[j])

    return {
        "critical_difference": float(cd),
        "matrix": matrix.tolist(),
        "solver_labels": list(range(k)),
    }


def anova_one_way(groups: list[np.ndarray]) -> dict[str, float]:
    """ANOVA de una via para comparar k grupos.

    Args:
        groups: Lista de arreglos, uno por solver/grupo.

    Returns:
        Dict con 'statistic' (F), 'p_value', 'df_between', 'df_within'.
    """
    result = f_oneway(*groups)

    k = len(groups)
    n_total = sum(len(g) for g in groups)
    df_between = k - 1
    df_within = n_total - k

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "df_between": int(df_between),
        "df_within": int(df_within),
    }
