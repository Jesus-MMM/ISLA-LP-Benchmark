"""
Tests para SensitivityAnalysis y SensitivityRange.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestSensitivityRange:
    """Tests para SensitivityRange."""

    def test_default_values(self):
        from src.analysis.sensitivity import SensitivityRange

        r = SensitivityRange(name="x", current=1.5)
        assert r.name == "x"
        assert r.current == 1.5
        assert r.lower is None
        assert r.upper is None
        assert r.reduced_cost is None
        assert r.dual_value is None

    def test_custom_values(self):
        from src.analysis.sensitivity import SensitivityRange

        r = SensitivityRange(
            name="y",
            current=2.0,
            lower=1.0,
            upper=3.0,
            reduced_cost=0.5,
            dual_value=1.5,
        )
        assert r.name == "y"
        assert r.current == 2.0
        assert r.lower == 1.0
        assert r.upper == 3.0
        assert r.reduced_cost == 0.5
        assert r.dual_value == 1.5


class TestSensitivityAnalysis:
    """Tests para SensitivityAnalysis."""

    def test_default_values(self):
        from src.analysis.sensitivity import SensitivityAnalysis

        analysis = SensitivityAnalysis()
        assert analysis.objective_ranges == []
        assert analysis.rhs_ranges == []
        assert analysis.bound_ranges == []

    def test_with_ranges(self):
        from src.analysis.sensitivity import SensitivityAnalysis, SensitivityRange

        analysis = SensitivityAnalysis(
            objective_ranges=[SensitivityRange(name="x", current=1.0)],
            rhs_ranges=[SensitivityRange(name="R1", current=10.0)],
        )
        assert len(analysis.objective_ranges) == 1
        assert len(analysis.rhs_ranges) == 1

    def test_get_objective_range_found(self):
        from src.analysis.sensitivity import SensitivityAnalysis, SensitivityRange

        analysis = SensitivityAnalysis(
            objective_ranges=[
                SensitivityRange(name="x", current=1.0),
                SensitivityRange(name="y", current=2.0),
            ],
        )
        result = analysis.get_objective_range("x")
        assert result is not None
        assert result.name == "x"

    def test_get_objective_range_not_found(self):
        from src.analysis.sensitivity import SensitivityAnalysis, SensitivityRange

        analysis = SensitivityAnalysis(
            objective_ranges=[SensitivityRange(name="x", current=1.0)],
        )
        result = analysis.get_objective_range("z")
        assert result is None

    def test_get_rhs_range_found(self):
        from src.analysis.sensitivity import SensitivityAnalysis, SensitivityRange

        analysis = SensitivityAnalysis(
            rhs_ranges=[
                SensitivityRange(name="R1", current=10.0),
                SensitivityRange(name="R2", current=20.0),
            ],
        )
        result = analysis.get_rhs_range("R2")
        assert result is not None
        assert result.current == 20.0

    def test_get_rhs_range_not_found(self):
        from src.analysis.sensitivity import SensitivityAnalysis, SensitivityRange

        analysis = SensitivityAnalysis(
            rhs_ranges=[SensitivityRange(name="R1", current=10.0)],
        )
        result = analysis.get_rhs_range("R3")
        assert result is None


class TestExtractHighsSensitivity:
    """Tests para extract_highs_sensitivity."""

    def test_extract_with_none_model(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        result = extract_highs_sensitivity(None)
        assert result is None

    def test_extract_with_none_solution(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        class MockHp:
            def getSolution(self):
                return None

        result = extract_highs_sensitivity(MockHp())
        assert result is None

    def test_extract_highs_success(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        class MockColInfo:
            cost = [2.0]
            lower = [0.0]
            upper = [10.0]

        class MockSolution:
            col_value = [1.0, 2.0]
            col_dual = [0.0, 0.5]
            row_dual = [1.5, 0.0]

        class MockHp:
            def getSolution(self):
                return MockSolution()
            def getNumCol(self):
                return 2
            def getNumRow(self):
                return 2
            def getColsByRange(self, i, j):
                return MockColInfo()
            def getRowsByRange(self, i, j):
                class MockRowInfo:
                    lower = [10.0]
                    upper = [10.0]
                return MockRowInfo()

        result = extract_highs_sensitivity(MockHp())
        assert result is not None
        assert len(result.objective_ranges) == 2
        assert len(result.rhs_ranges) == 2

    def test_extract_highs_exception(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        class MockHp:
            def getSolution(self):
                raise RuntimeError("mock error")

        result = extract_highs_sensitivity(MockHp())
        assert result is None

    def test_extract_highs_with_fallback(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        class MockColInfo:
            cost = [2.0]
            lower = [0.0]
            upper = [10.0]

        class MockSolution:
            col_value = [1.0]
            col_dual = [0.5]

        class MockHp:
            def getSolution(self):
                return MockSolution()
            def getNumCol(self):
                return 1
            def getNumRow(self):
                return 1
            def getColsByRange(self, i, j):
                return MockColInfo()
            def getRowsByRange(self, i, j):
                raise RuntimeError("no row info")

        result = extract_highs_sensitivity(MockHp())
        assert result is not None
        assert len(result.objective_ranges) == 1


class TestExtractGurobiSensitivity:
    """Tests para extract_gurobi_sensitivity."""

    def test_extract_with_none_model(self):
        from src.analysis.sensitivity import extract_gurobi_sensitivity

        result = extract_gurobi_sensitivity(None)
        assert result is None

    def test_extract_gurobi_success(self):
        from src.analysis.sensitivity import extract_gurobi_sensitivity

        class MockVar:
            def getAttr(self, attr):
                if attr == "SAObjLow":
                    return 1.0
                elif attr == "SAObjUp":
                    return 3.0
                elif attr == "RC":
                    return 0.0
                elif attr == "Obj":
                    return 2.0
                return None
            varName = "x"

        class MockConstr:
            def getAttr(self, attr):
                if attr == "SARHSLow":
                    return 10.0
                elif attr == "SARHSUp":
                    return 20.0
                elif attr == "Pi":
                    return 1.5
                elif attr == "RHS":
                    return 15.0
                return None
            constrName = "C1"

        class MockModel:
            def getVars(self):
                return [MockVar()]
            def getConstrs(self):
                return [MockConstr()]

        result = extract_gurobi_sensitivity(MockModel())
        assert result is not None
        assert len(result.objective_ranges) == 1
        assert len(result.rhs_ranges) == 1

    def test_extract_gurobi_exception(self):
        from src.analysis.sensitivity import extract_gurobi_sensitivity

        class MockVar:
            def getAttr(self, attr):
                raise RuntimeError("mock error")
            varName = "x"

        class MockModel:
            def getVars(self):
                return [MockVar()]
            def getConstrs(self):
                return []

        result = extract_gurobi_sensitivity(MockModel())
        assert result is None


class TestExtractGLPKSensitivity:
    """Tests para extract_glpk_sensitivity."""

    def test_extract_glpk_none_input(self):
        from src.analysis.sensitivity import extract_glpk_sensitivity

        result = extract_glpk_sensitivity(None, [], [])
        assert result is None

    def test_extract_glpk_exception(self):
        from src.analysis.sensitivity import extract_glpk_sensitivity

        class MockConstr:
            name = "R1"
            rhs = 10.0

        result = extract_glpk_sensitivity("not_real_prob", ["x"], [MockConstr()])
        assert result is None


class TestExtractHighsEdgeCases:
    """Tests para casos extremos de extract_highs_sensitivity."""

    def test_extract_highs_rc_large(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        class MockColInfo:
            cost = [2.0]
            lower = [0.0]
            upper = [10.0]

        class MockSolution:
            col_value = [0.0]
            col_dual = [-0.5]
            row_dual = []

        class MockHp:
            def getSolution(self):
                return MockSolution()
            def getNumCol(self):
                return 1
            def getNumRow(self):
                return 0
            def getColsByRange(self, i, j):
                return MockColInfo()

        result = extract_highs_sensitivity(MockHp())
        assert result is not None
        assert result.objective_ranges[0].lower is not None

    def test_extract_highs_rc_zero(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        class MockColInfo:
            cost = [2.0]
            lower = [0.0]
            upper = [10.0]

        class MockSolution:
            col_value = [10.0]
            col_dual = [0.0]
            row_dual = []

        class MockHp:
            def getSolution(self):
                return MockSolution()
            def getNumCol(self):
                return 1
            def getNumRow(self):
                return 0
            def getColsByRange(self, i, j):
                return MockColInfo()

        result = extract_highs_sensitivity(MockHp())
        assert result is not None

    def test_extract_highs_no_col_values(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        class MockColInfo:
            cost = [2.0]
            lower = [0.0]
            upper = [10.0]

        class MockSolution:
            col_value = None
            col_dual = [0.5]
            row_dual = []

        class MockHp:
            def getSolution(self):
                return MockSolution()
            def getNumCol(self):
                return 1
            def getNumRow(self):
                return 0
            def getColsByRange(self, i, j):
                return MockColInfo()

        result = extract_highs_sensitivity(MockHp())
        assert result is not None

    def test_extract_highs_no_row_dual(self):
        from src.analysis.sensitivity import extract_highs_sensitivity

        class MockColInfo:
            cost = [2.0]
            lower = [0.0]
            upper = [10.0]

        class MockSolution:
            col_value = [1.0]
            col_dual = [0.0]

        class MockHp:
            def getSolution(self):
                return MockSolution()
            def getNumCol(self):
                return 1
            def getNumRow(self):
                return 0

        result = extract_highs_sensitivity(MockHp())
        assert result is not None