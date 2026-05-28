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

        CVXOPT solo minimiza; objetivos max se niegan.
        Returns:
            dict con: c, G, h, A, b, constraint_order, sense
        """
        variables = list(problem.variables)
        c = np.array([problem.objective.get(v, 0.0) for v in variables], dtype=float)
        if problem.sense.lower() == "max":
            c = -c

        G_rows: list[list[float]] = []
        h_vals: list[float] = []
        constraint_order: list[str] = []

        for constr in problem.constraints:
            coeffs = [constr.coefficients.get(v, 0.0) for v in variables]
            name = constr.name or f"R{problem.constraints.index(constr)}"
            if constr.sense == "=":
                continue
            if constr.sense in (">=", ">"):
                G_rows.append([-x for x in coeffs])
                h_vals.append(-constr.rhs)
            else:
                G_rows.append(coeffs)
                h_vals.append(constr.rhs)
            constraint_order.append(name)

        n = len(variables)
        for var in variables:
            bound = problem.bounds.get(var)
            if bound:
                idx = variables.index(var)
                if bound.lower is not None:
                    row = [0.0] * n
                    row[idx] = -1.0
                    G_rows.append(row)
                    h_vals.append(-bound.lower)
                if bound.upper is not None:
                    row = [0.0] * n
                    row[idx] = 1.0
                    G_rows.append(row)
                    h_vals.append(bound.upper)

        A_rows: list[list[float]] = []
        b_vals: list[float] = []
        for constr in problem.constraints:
            if constr.sense == "=":
                A_rows.append([constr.coefficients.get(v, 0.0) for v in variables])
                b_vals.append(constr.rhs)

        return {
            "c": c,
            "G": np.array(G_rows, dtype=float) if G_rows else None,
            "h": np.array(h_vals, dtype=float) if h_vals else None,
            "A": np.array(A_rows, dtype=float) if A_rows else None,
            "b": np.array(b_vals, dtype=float) if b_vals else None,
            "constraint_order": constraint_order,
            "sense": problem.sense,
        }

    @staticmethod
    def to_osqp(problem: LinearProblem) -> dict[str, Any]:
        """
        Convierte a datos OSQP (P, q, A, l, u).

        Returns:
            dict con: P, q, A, l, u (sparse CSC arrays numpy), constraint_order
        """
        from scipy import sparse

        import numpy as np

        variables = list(problem.variables)
        n = len(variables)

        q = np.array([problem.objective.get(v, 0.0) for v in variables], dtype=float)
        if problem.sense.lower() == "max":
            q = -q

        A_rows: list[list[float]] = []
        l_vals: list[float] = []
        u_vals: list[float] = []
        constraint_order: list[str] = []

        for constr in problem.constraints:
            coeffs = [constr.coefficients.get(v, 0.0) for v in variables]
            name = constr.name or f"R{problem.constraints.index(constr)}"
            if constr.sense == "=":
                A_rows.append(coeffs)
                l_vals.append(constr.rhs)
                u_vals.append(constr.rhs)
            elif constr.sense in ("<=", "<"):
                A_rows.append(coeffs)
                l_vals.append(-np.inf)
                u_vals.append(constr.rhs)
            else:
                A_rows.append(coeffs)
                l_vals.append(constr.rhs)
                u_vals.append(np.inf)
            constraint_order.append(name)

        for var in variables:
            bound = problem.bounds.get(var)
            if bound:
                row = [0.0] * n
                row[variables.index(var)] = 1.0
                A_rows.append(row)
                lb = bound.lower if bound.lower is not None else -np.inf
                ub = bound.upper if bound.upper is not None else np.inf
                l_vals.append(lb)
                u_vals.append(ub)

        if A_rows:
            A = sparse.csc_matrix(np.array(A_rows, dtype=float))
            lb_array = np.array(l_vals, dtype=float)
            u = np.array(u_vals, dtype=float)
        else:
            A = sparse.csc_matrix((0, n))
            lb_array = np.array([])
            u = np.array([])

        P = sparse.csc_matrix((n, n))

        return {
            "P": P,
            "q": q,
            "A": A,
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
        from scipy import sparse

        import numpy as np

        variables = list(problem.variables)

        c = np.array([problem.objective.get(v, 0.0) for v in variables], dtype=float)
        if problem.sense.lower() == "max":
            c = -c

        A_ub_rows: list[list[float]] = []
        b_ub_vals: list[float] = []
        A_eq_rows: list[list[float]] = []
        b_eq_vals: list[float] = []

        for constr in problem.constraints:
            coeffs = [constr.coefficients.get(v, 0.0) for v in variables]
            if constr.sense in ("<=", "<"):
                A_ub_rows.append(coeffs)
                b_ub_vals.append(constr.rhs)
            elif constr.sense in (">=", ">"):
                A_ub_rows.append([-x for x in coeffs])
                b_ub_vals.append(-constr.rhs)
            else:
                A_eq_rows.append(coeffs)
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
            "A_ub": sparse.csr_matrix(np.array(A_ub_rows, dtype=float)) if A_ub_rows else None,
            "b_ub": np.array(b_ub_vals, dtype=float) if b_ub_vals else None,
            "A_eq": sparse.csr_matrix(np.array(A_eq_rows, dtype=float)) if A_eq_rows else None,
            "b_eq": np.array(b_eq_vals, dtype=float) if b_eq_vals else None,
            "bounds": bounds,
        }
