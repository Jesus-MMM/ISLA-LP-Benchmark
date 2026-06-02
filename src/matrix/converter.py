"""
Convierte LinearProblem a formatos de matriz específicos de cada solver.
Reduce la lógica duplicada de construcción de matrices en los solvers.
"""

from typing import Any

import numpy as np

from ..core import LinearProblem

INF = 1e30


class MatrixConverter:
    """Métodos estáticos para convertir LinearProblem a formatos de solver."""

    @staticmethod
    def to_highs(problem: LinearProblem) -> dict[str, Any]:
        """
        Convierte a datos compatibles con highspy.

        Returns:
            dict con: variables, objective, col_lower, col_upper,
                      row_lower, row_upper, row_indices, row_values
        """
        variables = list(problem.variables)
        obj = [problem.objective.get(v, 0.0) for v in variables]

        col_lower = []
        col_upper = []
        for v in variables:
            bound = problem.bounds.get(v)
            if bound:
                col_lower.append(bound.lower if bound.lower is not None else 0.0)
                col_upper.append(bound.upper if bound.upper is not None else INF)
            else:
                col_lower.append(0.0)
                col_upper.append(INF)

        row_lower: list[float] = []
        row_upper: list[float] = []
        row_indices: list[list[int]] = []
        row_values: list[list[float]] = []

        for constr in problem.constraints:
            coeffs = [constr.coefficients.get(v, 0.0) for v in variables]
            indices = [i for i, c in enumerate(coeffs) if abs(c) > 1e-14]
            vals = [coeffs[i] for i in indices]
            row_indices.append(indices)
            row_values.append(vals)
            if constr.sense == "<=":
                row_lower.append(-INF)
                row_upper.append(constr.rhs)
            elif constr.sense == ">=":
                row_lower.append(constr.rhs)
                row_upper.append(INF)
            else:
                row_lower.append(constr.rhs)
                row_upper.append(constr.rhs)

        result: dict[str, Any] = {
            "variables": variables,
            "objective": obj,
            "col_lower": col_lower,
            "col_upper": col_upper,
            "row_lower": row_lower,
            "row_upper": row_upper,
            "row_indices": row_indices,
            "row_values": row_values,
            "sense": problem.sense,
        }
        if problem.variable_types:
            result["variable_types"] = problem.variable_types
        return result

    @staticmethod
    def to_glpk(problem: LinearProblem) -> dict[str, Any]:
        """
        Convierte a datos compatibles con swiglpk.

        Returns:
            dict con: variables, objective, col_bounds, row_bounds,
                      ia (1-indexed), ja (1-indexed), ar
        """
        variables = list(problem.variables)
        obj = [problem.objective.get(v, 0.0) for v in variables]

        col_bounds: list[tuple[str, float, float]] = []
        for v in variables:
            bound = problem.bounds.get(v)
            if bound is None:
                col_bounds.append(("LO", 0.0, 0.0))
            elif bound.lower is not None and bound.upper is not None:
                if abs(bound.lower - bound.upper) < 1e-14:
                    col_bounds.append(("FX", bound.lower, bound.upper))
                else:
                    col_bounds.append(("DB", bound.lower, bound.upper))
            elif bound.lower is not None:
                col_bounds.append(("LO", bound.lower, 0.0))
            elif bound.upper is not None:
                col_bounds.append(("UP", 0.0, bound.upper))
            else:
                col_bounds.append(("FR", 0.0, 0.0))

        row_bounds: list[tuple[str, float, float]] = []
        ia: list[int] = []
        ja: list[int] = []
        ar: list[float] = []

        for i, constr in enumerate(problem.constraints):
            if constr.sense == "<=":
                row_bounds.append(("UP", 0.0, constr.rhs))
            elif constr.sense == ">=":
                row_bounds.append(("LO", constr.rhs, 0.0))
            else:
                row_bounds.append(("FX", constr.rhs, constr.rhs))
            for var, coeff in constr.coefficients.items():
                if abs(coeff) > 1e-14:
                    try:
                        j = variables.index(var)
                    except ValueError:
                        continue
                    ia.append(i + 1)
                    ja.append(j + 1)
                    ar.append(coeff)

        return {
            "variables": variables,
            "objective": obj,
            "col_bounds": col_bounds,
            "row_bounds": row_bounds,
            "ia": ia,
            "ja": ja,
            "ar": ar,
        }

    @staticmethod
    def to_cvxopt(problem: LinearProblem) -> dict[str, Any]:
        """
        Convierte a matrices CVXOPT (c, G, h, A, b).

        Construye usando coordenadas COO (solo no-ceros) para evitar
        la lista de listas densa intermedia. CVXOPT recibe matrices densas.
        CVXOPT solo minimiza; objetivos max se niegan.
        Returns:
            dict con: c, G, h, A, b, constraint_order, sense
        """
        from scipy import sparse

        variables = list(problem.variables)
        n = len(variables)
        c = np.array([problem.objective.get(v, 0.0) for v in variables], dtype=float)
        if problem.sense.lower() == "max":
            c = -c

        g_data: list[float] = []
        g_rows: list[int] = []
        g_cols: list[int] = []
        h_vals: list[float] = []
        constraint_order: list[str] = []
        n_ineq = 0

        for constr in problem.constraints:
            name = constr.name or f"R{problem.constraints.index(constr)}"
            if constr.sense == "=":
                continue
            for var, coeff in constr.coefficients.items():
                if abs(coeff) > 1e-14:
                    try:
                        j = variables.index(var)
                    except ValueError:
                        continue
                    actual = -coeff if constr.sense in (">=", ">") else coeff
                    g_data.append(actual)
                    g_rows.append(n_ineq)
                    g_cols.append(j)
            if constr.sense in (">=", ">"):
                h_vals.append(-constr.rhs)
            else:
                h_vals.append(constr.rhs)
            constraint_order.append(name)
            n_ineq += 1

        for var in variables:
            bound = problem.bounds.get(var)
            if bound:
                idx = variables.index(var)
                if bound.lower is not None:
                    g_data.append(-1.0)
                    g_rows.append(n_ineq)
                    g_cols.append(idx)
                    h_vals.append(-bound.lower)
                    n_ineq += 1
                if bound.upper is not None:
                    g_data.append(1.0)
                    g_rows.append(n_ineq)
                    g_cols.append(idx)
                    h_vals.append(bound.upper)
                    n_ineq += 1

        if n_ineq > 0:
            g_mat = sparse.csc_matrix((g_data, (g_rows, g_cols)), shape=(n_ineq, n))
            g_mat = g_mat.toarray()
            h = np.array(h_vals, dtype=float)
        else:
            g_mat = None
            h = None

        a_data: list[float] = []
        a_rows: list[int] = []
        a_cols: list[int] = []
        b_vals: list[float] = []
        n_eq = 0

        for constr in problem.constraints:
            if constr.sense != "=":
                continue
            for var, coeff in constr.coefficients.items():
                if abs(coeff) > 1e-14:
                    try:
                        j = variables.index(var)
                    except ValueError:
                        continue
                    a_data.append(coeff)
                    a_rows.append(n_eq)
                    a_cols.append(j)
            b_vals.append(constr.rhs)
            n_eq += 1

        if n_eq > 0:
            a_mat = sparse.csc_matrix((a_data, (a_rows, a_cols)), shape=(n_eq, n))
            a_mat = a_mat.toarray()
            b = np.array(b_vals, dtype=float)
        else:
            a_mat = None
            b = None

        return {
            "c": c,
            "G": g_mat,
            "h": h,
            "A": a_mat,
            "b": b,
            "constraint_order": constraint_order,
            "sense": problem.sense,
        }

    @staticmethod
    def to_osqp(problem: LinearProblem) -> dict[str, Any]:
        """
        Convierte a datos OSQP (P, q, A, l, u).

        Construye usando coordenadas COO (solo no-ceros) para evitar
        la lista de listas densa intermedia.
        Returns:
            dict con: P, q, A, l, u (sparse CSC arrays numpy), constraint_order
        """
        import numpy as np
        from scipy import sparse

        variables = list(problem.variables)
        n = len(variables)

        q = np.array([problem.objective.get(v, 0.0) for v in variables], dtype=float)
        if problem.sense.lower() == "max":
            q = -q

        a_data: list[float] = []
        a_rows: list[int] = []
        a_cols: list[int] = []
        l_vals: list[float] = []
        u_vals: list[float] = []
        constraint_order: list[str] = []
        n_rows = 0

        for i, constr in enumerate(problem.constraints):
            name = constr.name or f"R{i}"
            for var, coeff in constr.coefficients.items():
                if abs(coeff) > 1e-14:
                    try:
                        j = variables.index(var)
                    except ValueError:
                        continue
                    a_data.append(coeff)
                    a_rows.append(n_rows)
                    a_cols.append(j)
            if constr.sense == "=":
                l_vals.append(constr.rhs)
                u_vals.append(constr.rhs)
            elif constr.sense in ("<=", "<"):
                l_vals.append(-np.inf)
                u_vals.append(constr.rhs)
            else:
                l_vals.append(constr.rhs)
                u_vals.append(np.inf)
            constraint_order.append(name)
            n_rows += 1

        for var in variables:
            bound = problem.bounds.get(var)
            if bound:
                a_data.append(1.0)
                a_rows.append(n_rows)
                a_cols.append(variables.index(var))
                lb = bound.lower if bound.lower is not None else -np.inf
                ub = bound.upper if bound.upper is not None else np.inf
                l_vals.append(lb)
                u_vals.append(ub)
                n_rows += 1

        if n_rows > 0:
            a_mat = sparse.csc_matrix((a_data, (a_rows, a_cols)), shape=(n_rows, n))
            lb_array = np.array(l_vals, dtype=float)
            u = np.array(u_vals, dtype=float)
        else:
            a_mat = sparse.csc_matrix((0, n))
            lb_array = np.array([])
            u = np.array([])

        p_mat = sparse.csc_matrix((n, n))

        return {
            "P": p_mat,
            "q": q,
            "A": a_mat,
            "l": lb_array,
            "u": u,
            "constraint_order": constraint_order,
            "sense": problem.sense,
        }

    @staticmethod
    def to_scipy(problem: LinearProblem) -> dict[str, Any]:
        """
        Convierte a matrices sparse scipy (linprog format).

        Returns:
            dict con: c, A_ub, b_ub, A_eq, b_eq, bounds
        """
        import numpy as np
        from scipy import sparse

        variables = list(problem.variables)

        c = np.array([problem.objective.get(v, 0.0) for v in variables], dtype=float)
        if problem.sense.lower() == "max":
            c = -c

        a_ub_rows: list[list[float]] = []
        b_ub_vals: list[float] = []
        a_eq_rows: list[list[float]] = []
        b_eq_vals: list[float] = []

        for constr in problem.constraints:
            coeffs = [constr.coefficients.get(v, 0.0) for v in variables]
            if constr.sense in ("<=", "<"):
                a_ub_rows.append(coeffs)
                b_ub_vals.append(constr.rhs)
            elif constr.sense in (">=", ">"):
                a_ub_rows.append([-x for x in coeffs])
                b_ub_vals.append(-constr.rhs)
            else:
                a_eq_rows.append(coeffs)
                b_eq_vals.append(constr.rhs)

        bounds: list[tuple[float | None, float | None]] = []
        for var in variables:
            bound = problem.bounds.get(var)
            if bound:
                bounds.append((bound.lower, bound.upper))
            else:
                bounds.append((0.0, None))

        return {
            "c": c,
            "A_ub": sparse.csr_matrix(np.array(a_ub_rows, dtype=float)) if a_ub_rows else None,
            "b_ub": np.array(b_ub_vals, dtype=float) if b_ub_vals else None,
            "A_eq": sparse.csr_matrix(np.array(a_eq_rows, dtype=float)) if a_eq_rows else None,
            "b_eq": np.array(b_eq_vals, dtype=float) if b_eq_vals else None,
            "bounds": bounds,
        }
