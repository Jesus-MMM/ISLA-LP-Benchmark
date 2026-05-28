"""
Parser para problemas de programación lineal en formato texto.
Soporta expresiones multi-línea, comentarios inline y nombres con caracteres especiales.
"""

from ..core import LinearProblem, LinearConstraint, VariableBound
import re

TERM_PATTERN = re.compile(
    r"([+-]?)((?:\d+\.?\d*|\d*\.?\d+)(?:[eE][+-]?\d+)?|)([a-zA-Z][a-zA-Z0-9_]*)"
)
BOUND_SIMPLE = re.compile(r"([a-zA-Z]\w*)(<=|>=)(-?\d*\.?\d+(?:[eE][+-]?\d+)?)")
BOUND_DOUBLE = re.compile(r"(-?\d*\.?\d+(?:[eE][+-]?\d+)?)<=([a-zA-Z]\w*)<=(-?\d*\.?\d+(?:[eE][+-]?\d+)?)")
BOUND_FREE = re.compile(r"([a-zA-Z]\w*)\s+(free|unrestricted)", re.IGNORECASE)
BOUND_LEFT = re.compile(r"(-?\d*\.?\d+(?:[eE][+-]?\d+)?)<=([a-zA-Z]\w*)")
BOUND_RIGHT = re.compile(r"([a-zA-Z]\w*)<=(-?\d*\.?\d+(?:[eE][+-]?\d+)?)")


_INLINE_COMMENT_RE = re.compile(r"\\\*.*?\*\\|#.*$")


class LPParser:
    """
    Parser para problemas de programación lineal desde texto.

    ### atributos:
    - txt: str - Texto con la definición del problema de PL.
    - bounds: dict[str, VariableBound] - Diccionario de límites de variables.
    """

    def __init__(self, txt: str) -> None:
        self.txt = txt
        self.bounds: dict[str, VariableBound] = {}

    @staticmethod
    def _strip_comments(line: str) -> str:
        """Elimina comentarios \\*...*\\ y # de una línea."""
        line = _INLINE_COMMENT_RE.sub("", line)
        return line.strip()

    def _preprocess_lines(self, text: str) -> list[str]:
        """Preprocesa el texto: elimina comentarios y une líneas continuadas."""
        raw_lines = text.splitlines()
        processed: list[str] = []
        current = ""

        for raw_line in raw_lines:
            line = self._strip_comments(raw_line)
            if not line:
                continue
            if line.endswith("\\"):
                current += line[:-1] + " "
                continue
            if current:
                current += line
                processed.append(current)
                current = ""
            else:
                processed.append(line)
        if current:
            processed.append(current)
        return processed

    def parse(self) -> LinearProblem:
        """
        Parsea el problema de PL desde el texto proporcionado.

        Returns:
            LinearProblem: Instancia representando el problema parseado.

        Raises:
            ValueError: Si el formato es inválido.
        """
        lines = self._preprocess_lines(self.txt)

        if not lines:
            raise ValueError("Falta la función objetivo")

        objective_line = lines[0].strip()
        if not objective_line:
            raise ValueError("Falta la función objetivo")

        sense, objective_coeffs = self._parse_objective(objective_line)

        constraints: list[LinearConstraint] = []
        variable_types: dict[str, str] = {}

        for i, line in enumerate(lines[1:]):
            line = line.strip()
            if not line:
                continue
            if self._could_be_bound(line):
                self._parse_bound(line)
                for var, bound in self.bounds.items():
                    if bound.variable_type != "continuous":
                        variable_types[var] = bound.variable_type
                continue
            constraint = self._parse_constraint(line)
            if not constraint.name:
                constraint.name = f"R{i}"
            constraints.append(constraint)

        variables = sorted({
            *self._extract_variables(objective_coeffs, constraints),
            *self.bounds.keys()
        })

        if not objective_coeffs:
            raise ValueError("La función objetivo no puede estar vacía")

        if not constraints:
            raise ValueError("Se requiere al menos una restricción")

        return LinearProblem(
            objective=objective_coeffs,
            sense=sense,
            constraints=constraints,
            variables=variables,
            bounds=self.bounds,
            variable_types=variable_types
        )

    def _parse_objective(self, line: str) -> tuple[str, dict[str, float]]:
        """Parsea la función objetivo."""
        parts = line.split(maxsplit=1)

        if len(parts) != 2:
            raise ValueError(f"Función objetivo inválida: {line}")

        sense = parts[0].replace(":", "").lower().strip()

        sense_clean = sense.replace("imize", "").replace("imizar", "").strip()

        if sense_clean not in {"max", "min"}:
            if "max" in sense.lower():
                sense = "max"
            elif "min" in sense.lower():
                sense = "min"
            else:
                raise ValueError(f"Dirección de optimización inválida: {sense}")

        expr = parts[1]

        if "=" in expr:
            expr = expr.split("=", 1)[1]

        coefficients = self._parse_linear_expression(expr)

        return sense, coefficients

    def _parse_constraint(self, line: str) -> LinearConstraint:
        """Parsea una restricción."""
        c_name = ""

        colon_pos = line.find(":")
        if colon_pos > 0 and not self._is_numeric_at(line, colon_pos - 1):
            potential_name = line[:colon_pos].strip()
            if re.match(r"^[a-zA-Z][a-zA-Z0-9_\-\. ]*$", potential_name):
                c_name = potential_name
                line = line[colon_pos + 1:].strip()

        if "<=" in line:
            lhs, rhs = line.split("<=", 1)
            sense = "<="
        elif ">=" in line:
            lhs, rhs = line.split(">=", 1)
            sense = ">="
        elif "=" in line and not line.startswith("="):
            eq_pos = line.find("=")
            if eq_pos > 0 and line[eq_pos - 1] not in (">", "<"):
                lhs, rhs = line.split("=", 1)
                sense = "="
            else:
                raise ValueError(f"Restricción inválida: {line}")
        else:
            raise ValueError(f"Restricción inválida: {line}")

        coefficients = self._parse_linear_expression(lhs.strip())

        try:
            rhs_value = float(rhs.strip().rstrip(";"))
        except ValueError:
            raise ValueError(f"Valor RHS inválido en restricción: {line}")

        return LinearConstraint(
            coefficients=coefficients,
            rhs=rhs_value,
            sense=sense,
            name=c_name,
        )

    @staticmethod
    def _is_numeric_at(line: str, pos: int) -> bool:
        return pos >= 0 and line[pos].isdigit()

    def _extract_variables(self,
                           objective: dict[str, float],
                           constraints: list[LinearConstraint]
                           ) -> list[str]:
        variables: set[str] = set(objective.keys())
        for constraint in constraints:
            variables.update(constraint.coefficients.keys())
        return sorted(variables)

    def _parse_linear_expression(self, expr: str) -> dict[str, float]:
        if not expr.strip():
            raise ValueError("Expresión lineal vacía")

        expr = expr.replace(" ", "").rstrip(";").lstrip("+")
        expr = expr.replace("-", "+-")

        terms = expr.split("+")
        coefficients: dict[str, float] = {}

        for term in terms:
            term = term.strip()
            if not term:
                continue

            match = TERM_PATTERN.fullmatch(term)

            if not match:
                raise ValueError(f"Término inválido: {term}")

            sign_str, coeff_str, var = match.groups()

            sign = -1.0 if sign_str == "-" else 1.0

            if coeff_str == "":
                coeff = 1.0
            else:
                coeff = float(coeff_str)

            coefficients[var] = coefficients.get(var, 0) + sign * coeff

        return coefficients

    def _could_be_bound(self, line: str) -> bool:
        line_clean = line.replace(" ", "")
        if "free" in line.lower() or "unrestricted" in line.lower():
            return True
        if "<=" in line_clean or ">=" in line_clean:
            parts = line_clean.replace("<=", " ").replace(">=", " ").split()
            if len(parts) >= 2:
                lhs = parts[0].strip()
                if re.match(r"^[a-zA-Z]\w*$", lhs):
                    return True
                if re.match(r"^-?\d*\.?\d+(?:[eE][+-]?\d+)?$", lhs):
                    return True
                if len(parts) == 3 and re.match(r"^[a-zA-Z]\w*$", parts[1]):
                    return True
        return False

    def _parse_bound(self, line: str) -> None:
        line_for_type = line.lower()
        var_type = "continuous"
        if " integer" in line_for_type or " int " in line_for_type or line_for_type.endswith(" int") or line_for_type.endswith(" integer"):
            var_type = "integer"
            line = line.rsplit(" integer", 1)[0].rsplit(" int", 1)[0]
        elif " binary" in line_for_type or " bin " in line_for_type or line_for_type.endswith(" bin") or line_for_type.endswith(" binary"):
            var_type = "binary"
            line = line.rsplit(" binary", 1)[0].rsplit(" bin", 1)[0]

        free_match = BOUND_FREE.match(line)

        if free_match:
            var = free_match.group(1)
            self.bounds[var] = VariableBound(variable=var,
                                              lower=None,
                                              upper=None,
                                              variable_type=var_type)
            return

        line = line.replace(" ", "")

        match = BOUND_DOUBLE.match(line)

        if match:
            lower, var, upper = match.groups()
            bound = self.bounds.get(var, VariableBound(var))
            bound.lower = float(lower)
            bound.upper = float(upper)
            bound.variable_type = var_type
            self.bounds[var] = bound
            return

        match = BOUND_SIMPLE.match(line)

        if match:
            var, op, value = match.groups()
            value = float(value)
            bound = self.bounds.get(var, VariableBound(var))
            if op == ">=":
                bound.lower = value
            else:
                bound.upper = value
            bound.variable_type = var_type
            self.bounds[var] = bound
            return

        match = BOUND_LEFT.match(line)

        if match:
            lower, var = match.groups()
            bound = self.bounds.get(var, VariableBound(var))
            bound.lower = float(lower)
            bound.variable_type = var_type
            self.bounds[var] = bound
            return

        match = BOUND_RIGHT.match(line)

        if match:
            var, upper = match.groups()
            bound = self.bounds.get(var, VariableBound(var))
            bound.upper = float(upper)
            bound.variable_type = var_type
            self.bounds[var] = bound
            return

        raise ValueError(f"Formato de bound inválido: {line}")