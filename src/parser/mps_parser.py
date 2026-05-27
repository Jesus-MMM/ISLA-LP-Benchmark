"""
Parser para problemas de programación lineal en formato MPS.
"""

import re
from dataclasses import dataclass
from typing import Optional

from ..core import LinearProblem, LinearConstraint, VariableBound

ROW_TYPE_N = "N"
ROW_TYPE_L = "L"
ROW_TYPE_G = "G"
ROW_TYPE_E = "E"

BOUND_TYPE_FR = "FR"
BOUND_TYPE_LO = "LO"
BOUND_TYPE_UP = "UP"
BOUND_TYPE_FX = "FX"
BOUND_TYPE_MI = "MI"
BOUND_TYPE_PL = "PL"
BOUND_TYPE_BV = "BV"
BOUND_TYPE_LI = "LI"
BOUND_TYPE_UI = "UI"
BOUND_TYPE_SC = "SC"


@dataclass
class _MPSRow:
    name: str
    sense: str


@dataclass
class _MPSEntry:
    row: str
    value: float


@dataclass
class _MPSBound:
    bound_type: str
    variable: str
    value: Optional[float] = None


class MPSParser:
    """
    Parser para problemas de programación lineal en formato MPS.

    Soporta las secciones: ROWS, COLUMNS, RHS, BOUNDS, RANGES.
    Soporta marcadores INTORG/INTEND para variables enteras.
    """

    def __init__(self, txt: str) -> None:
        self.txt = txt
        self._rows: dict[str, _MPSRow] = {}
        self._cols: dict[str, list[_MPSEntry]] = {}
        self._rhs: dict[str, list[_MPSEntry]] = {}
        self._bounds: list[_MPSBound] = []
        self._ranges: list[_MPSEntry] = []
        self._integer_vars: set[str] = set()
        self._inside_int = False

    def parse(self) -> LinearProblem:
        self._rows.clear()
        self._cols.clear()
        self._rhs.clear()
        self._bounds.clear()
        self._ranges.clear()
        self._integer_vars.clear()
        self._inside_int = False

        lines = self.txt.strip().splitlines()
        self._parse_sections(lines)
        return self._build_problem()

    def parse_file(self, path: str) -> LinearProblem:
        with open(path, "r", encoding="utf-8") as f:
            self.txt = f.read()
        return self.parse()

    def _parse_sections(self, lines: list[str]) -> None:
        current_section = ""
        rhs_name = ""

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            upper_line = line.upper().strip()

            if upper_line == "ENDATA":
                break

            if line.startswith("*"):
                continue

            if upper_line == "ROWS":
                current_section = "ROWS"
                continue
            elif upper_line == "COLUMNS":
                current_section = "COLUMNS"
                continue
            elif upper_line == "RHS":
                current_section = "RHS"
                continue
            elif upper_line == "BOUNDS":
                current_section = "BOUNDS"
                continue
            elif upper_line == "RANGES":
                current_section = "RANGES"
                continue
            elif upper_line.startswith("NAME"):
                current_section = "NAME"
                continue

            stripped = line.strip()
            if not stripped:
                continue

            if current_section == "ROWS":
                self._parse_row(stripped)
            elif current_section == "COLUMNS":
                self._parse_column(stripped)
            elif current_section == "RHS":
                rhs_name = self._parse_rhs(stripped, rhs_name)
            elif current_section == "BOUNDS":
                self._parse_bound(stripped)
            elif current_section == "RANGES":
                self._parse_range(stripped)

    def _parse_row(self, line: str) -> None:
        if len(line) < 2:
            return
        row_type = line[0].upper()
        name = line[1:].strip()
        if row_type in (ROW_TYPE_N, ROW_TYPE_L, ROW_TYPE_G, ROW_TYPE_E):
            self._rows[name] = _MPSRow(name=name, sense=row_type)

    def _parse_column(self, line: str) -> None:
        fields = self._split_mps_fields(line)
        if len(fields) < 2:
            return

        var = fields[0]
        row = fields[1]

        if row.upper() in ("'MARKER'", "MARKER"):
            marker_idx = 3 if len(fields) >= 4 and fields[2].upper() not in ("INTORG", "INTEND") else 2
            if len(fields) > marker_idx:
                marker_type = fields[marker_idx].upper().strip("'")
                if marker_type == "INTORG":
                    self._inside_int = True
                elif marker_type == "INTEND":
                    self._inside_int = False
            return

        value = float(fields[2]) if len(fields) >= 3 else 0.0

        if var not in self._cols:
            self._cols[var] = []
            var_is_integer = self._inside_int
            if var_is_integer:
                self._integer_vars.add(var)

        self._cols[var].append(_MPSEntry(row=row, value=value))

        if len(fields) >= 5:
            row2 = fields[3]
            value2 = float(fields[4])
            self._cols[var].append(_MPSEntry(row=row2, value=value2))

    def _split_mps_fields(self, line: str) -> list[str]:
        fields = re.findall(r"'(?:[^']*)'|\S+", line)
        fields = [f.strip("'") for f in fields]
        return fields

    def _parse_rhs(self, line: str, rhs_name: str) -> str:
        fields = self._split_mps_fields(line)
        if not fields:
            return rhs_name

        name = fields[0]
        if len(fields) < 2:
            return name

        row = fields[1]
        value = float(fields[2])

        if name not in self._rhs:
            self._rhs[name] = []
        self._rhs[name].append(_MPSEntry(row=row, value=value))

        if len(fields) >= 5:
            row2 = fields[3]
            value2 = float(fields[4])
            self._rhs[name].append(_MPSEntry(row=row2, value=value2))

        return name

    def _parse_bound(self, line: str) -> None:
        fields = self._split_mps_fields(line)
        if len(fields) < 3:
            return

        bound_type = fields[0].upper()
        variable = fields[2]
        value = float(fields[3]) if len(fields) >= 4 else None

        self._bounds.append(_MPSBound(
            bound_type=bound_type,
            variable=variable,
            value=value,
        ))

    def _parse_range(self, line: str) -> None:
        fields = self._split_mps_fields(line)
        if len(fields) < 3:
            return

        row = fields[1]
        value = float(fields[2])

        self._ranges.append(_MPSEntry(row=row, value=value))

        if len(fields) >= 5:
            row2 = fields[3]
            value2 = float(fields[4])
            self._ranges.append(_MPSEntry(row=row2, value=value2))

    def _build_problem(self) -> LinearProblem:
        objective_name = None
        for row in self._rows.values():
            if row.sense == ROW_TYPE_N:
                objective_name = row.name
                break

        if objective_name is None:
            raise ValueError("No se encontró una fila tipo N (objetivo) en la sección ROWS")

        objective: dict[str, float] = {}
        constraint_coeffs: dict[str, dict[str, float]] = {}
        constraint_senses: dict[str, str] = {}
        constraint_names_order: list[str] = []

        for row_name, row in self._rows.items():
            if row_name == objective_name:
                continue
            constraint_coeffs[row_name] = {}
            constraint_senses[row_name] = self._sense_from_row_type(row.sense)
            constraint_names_order.append(row_name)

        for var, entries in self._cols.items():
            for entry in entries:
                if entry.row == objective_name:
                    objective[var] = objective.get(var, 0) + entry.value
                elif entry.row in constraint_coeffs:
                    constraint_coeffs[entry.row][var] = \
                        constraint_coeffs[entry.row].get(var, 0) + entry.value

        rhs_name = list(self._rhs.keys())[0] if self._rhs else ""
        rhs_values: dict[str, float] = {}
        if rhs_name and rhs_name in self._rhs:
            for entry in self._rhs[rhs_name]:
                rhs_values[entry.row] = entry.value

        ranges: dict[str, float] = {}
        for entry in self._ranges:
            ranges[entry.row] = entry.value

        constraints: list[LinearConstraint] = []
        for row_name in constraint_names_order:
            coeffs = constraint_coeffs[row_name]
            rhs = rhs_values.get(row_name, 0.0)
            sense = constraint_senses[row_name]

            if row_name in ranges:
                range_val = abs(ranges[row_name])
                if sense == "<=":
                    rhs = rhs + range_val
                elif sense == ">=":
                    rhs = rhs - range_val

            constraints.append(LinearConstraint(
                coefficients={k: v for k, v in coeffs.items() if v != 0},
                rhs=rhs,
                sense=sense,
                name=row_name,
            ))

        all_vars = sorted(set(
            list(objective.keys()) + [
                v for c in constraint_coeffs.values() for v in c.keys()
            ]
        ))

        bounds: dict[str, VariableBound] = {}
        for var in all_vars:
            bounds[var] = VariableBound(variable=var, lower=0.0, upper=None)

        for b in self._bounds:
            var = b.variable
            if var not in bounds:
                bounds[var] = VariableBound(variable=var, lower=None, upper=None)

            bt = b.bound_type
            if bt == BOUND_TYPE_FR:
                bounds[var].lower = None
                bounds[var].upper = None
            elif bt == BOUND_TYPE_LO:
                bounds[var].lower = b.value
            elif bt == BOUND_TYPE_UP:
                bounds[var].upper = b.value
            elif bt == BOUND_TYPE_FX:
                bounds[var].lower = b.value
                bounds[var].upper = b.value
            elif bt == BOUND_TYPE_MI:
                bounds[var].lower = None
            elif bt == BOUND_TYPE_PL:
                bounds[var].upper = None
            elif bt == BOUND_TYPE_BV:
                bounds[var].lower = 0.0
                bounds[var].upper = 1.0

        variable_types: dict[str, str] = {}
        for var in all_vars:
            if var in self._integer_vars:
                variable_types[var] = "integer"

        for b in self._bounds:
            if b.bound_type == BOUND_TYPE_BV:
                variable_types[b.variable] = "binary"
            elif b.bound_type in (BOUND_TYPE_LI, BOUND_TYPE_UI):
                variable_types[b.variable] = "integer"

        if not constraints:
            raise ValueError("Se requiere al menos una restricción")

        if not objective:
            raise ValueError("La función objetivo no puede estar vacía")

        return LinearProblem(
            objective=objective,
            sense="max",
            constraints=constraints,
            variables=all_vars,
            bounds=bounds,
            variable_types=variable_types,
        )

    def _sense_from_row_type(self, row_type: str) -> str:
        if row_type == ROW_TYPE_E:
            return "="
        elif row_type == ROW_TYPE_G:
            return ">="
        else:
            return "<="
