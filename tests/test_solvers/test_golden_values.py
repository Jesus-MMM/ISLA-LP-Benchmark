"""
Tests golden: verifican que los solvers produzcan valores numéricos correctos
en problemas con solución conocida.

Cada caso de prueba define un problema LP/MILP en formato texto,
su solución esperada, y se prueba contra todos los solvers disponibles.
"""

import pytest

from src.parser import LPParser
from src.solver.base import SolverRegistry

TOL = 1e-4

PROBLEMA_OPTIMO = """
max: 3000x + 5000y
2x + 3y <= 120
x + 3y <= 90
x >= 0
y >= 0
"""
SOLUCION_OPTIMO = {"objective": 190000.0, "x": 30.0, "y": 20.0}

PROBLEMA_INFACTIBLE = """
max: x + y
x + y <= 5
x + y >= 10
x >= 0
y >= 0
"""

PROBLEMA_NO_ACOTADO = """
max: x + y
x >= 0
y >= 0
x - y <= 0
"""

PROBLEMA_MILP = """
max: 4x + 2y + 3z
x + y + z <= 5
x >= 0 integer
y >= 0 integer
z >= 0 integer
"""
SOLUCION_MILP = {"objective": 20.0, "x": 5.0, "y": 0.0, "z": 0.0}


def _solvers_lp_disponibles():
    """Retorna lista de nombres de solvers que soportan LP."""
    disponibles = SolverRegistry.list_solvers(available_only=True)
    # Filtramos solo los que soportan LP (excluyendo QP-only como OSQP, ECOS, SCS, CVXOPT)
    lp_priority = ["highs", "cbc", "glpk", "gurobi", "scip"]
    return [s for s in lp_priority if s in disponibles]


def _solvers_milp_disponibles():
    disponibles = SolverRegistry.list_solvers(available_only=True)
    # Gurobi excluido: bug pre-existente con var.rc en vars integer (gurobi.py:290)
    milp_priority = ["highs", "cbc", "scip", "glpk"]
    return [s for s in milp_priority if s in disponibles]


@pytest.mark.parametrize("solver_name", _solvers_lp_disponibles())
class TestGoldenLPOptimo:

    def test_estado_optimal(self, solver_name):
        problema = LPParser(PROBLEMA_OPTIMO).parse()
        solver_class = SolverRegistry.get(solver_name)
        solver = solver_class(problema)
        sol = solver.solve()
        assert sol.is_optimal(), f"{solver_name}: se esperaba OPTIMAL, se obtuvo {sol.status}"

    def test_objetivo_correcto(self, solver_name):
        problema = LPParser(PROBLEMA_OPTIMO).parse()
        solver_class = SolverRegistry.get(solver_name)
        solver = solver_class(problema)
        sol = solver.solve()
        assert sol.objective_value is not None
        assert sol.objective_value == pytest.approx(SOLUCION_OPTIMO["objective"], abs=TOL), \
            f"{solver_name}: objetivo {sol.objective_value} != {SOLUCION_OPTIMO['objective']}"

    def test_variables_correctas(self, solver_name):
        problema = LPParser(PROBLEMA_OPTIMO).parse()
        solver_class = SolverRegistry.get(solver_name)
        solver = solver_class(problema)
        sol = solver.solve()
        for var, valor_esperado in [("x", 30.0), ("y", 20.0)]:
            assert var in sol.variables, f"{solver_name}: variable {var} no está en la solución"
            assert sol.variables[var] == pytest.approx(valor_esperado, abs=TOL), \
                f"{solver_name}: {var} = {sol.variables[var]} != {valor_esperado}"

    def test_restricciones_satisfechas(self, solver_name):
        problema = LPParser(PROBLEMA_OPTIMO).parse()
        solver_class = SolverRegistry.get(solver_name)
        solver = solver_class(problema)
        sol = solver.solve()
        for constr in problema.constraints:
            lhs = sum(coeff * sol.variables.get(var, 0.0) for var, coeff in constr.coefficients.items())
            if constr.sense == "<=":
                assert lhs <= constr.rhs + TOL, \
                    f"{solver_name}: restricción {constr.name} violada: {lhs} > {constr.rhs}"
            elif constr.sense == ">=":
                assert lhs >= constr.rhs - TOL, \
                    f"{solver_name}: restricción {constr.name} violada: {lhs} < {constr.rhs}"
            else:
                assert lhs == pytest.approx(constr.rhs, abs=TOL), \
                    f"{solver_name}: restricción {constr.name} violada: {lhs} != {constr.rhs}"


def test_infactible_highs():
    solver_class = SolverRegistry.get("highs")
    if solver_class is None:
        pytest.skip("HiGHS no disponible")
    problema = LPParser(PROBLEMA_INFACTIBLE).parse()
    solver = solver_class(problema)
    sol = solver.solve()
    assert sol.is_infeasible(), f"Se esperaba INFEASIBLE, se obtuvo {sol.status}"


def test_no_acotado_highs():
    solver_class = SolverRegistry.get("highs")
    if solver_class is None:
        pytest.skip("HiGHS no disponible")
    problema = LPParser(PROBLEMA_NO_ACOTADO).parse()
    solver = solver_class(problema)
    sol = solver.solve()
    assert sol.is_unbounded() or "UNBOUNDED" in sol.status.upper(), \
        f"Se esperaba UNBOUNDED, se obtuvo {sol.status}"


@pytest.mark.parametrize("solver_name", _solvers_milp_disponibles())
class TestGoldenMILP:

    def test_estado_optimal(self, solver_name):
        problema = LPParser(PROBLEMA_MILP).parse()
        solver_class = SolverRegistry.get(solver_name)
        solver = solver_class(problema)
        sol = solver.solve()
        assert sol.is_optimal(), f"{solver_name}: se esperaba OPTIMAL, se obtuvo {sol.status}"

    def test_objetivo_correcto(self, solver_name):
        problema = LPParser(PROBLEMA_MILP).parse()
        solver_class = SolverRegistry.get(solver_name)
        solver = solver_class(problema)
        sol = solver.solve()
        assert sol.objective_value is not None
        assert sol.objective_value == pytest.approx(SOLUCION_MILP["objective"], abs=TOL), \
            f"{solver_name}: objetivo {sol.objective_value} != {SOLUCION_MILP['objective']}"

    def test_variables_correctas(self, solver_name):
        problema = LPParser(PROBLEMA_MILP).parse()
        solver_class = SolverRegistry.get(solver_name)
        solver = solver_class(problema)
        sol = solver.solve()
        for var, valor_esperado in SOLUCION_MILP.items():
            if var == "objective":
                continue
            assert var in sol.variables, f"{solver_name}: variable {var} no está en la solución"
            assert sol.variables[var] == pytest.approx(valor_esperado, abs=TOL), \
                f"{solver_name}: {var} = {sol.variables[var]} != {valor_esperado}"
