"""
Módulo para parsear múltiples problemas de programación lineal.
Los problemas deben estar separados por una línea con '---' o '==='.
"""


from ..core import LinearProblem
from ..core.exceptions import LPParseError
from .lp_parser import LPParser


class MultiLPParser:
    """Parser para múltiples problemas de programación lineal."""

    # Delimitadores reconocidos para separar problemas
    DELIMITERS = ['---', '===', '___']

    def __init__(self, txt: str) -> None:
        """
        Inicializa el parser multi-problema.

        Args:
            txt: Texto con múltiples problemas separados por delimitadores.
        """
        self.txt = txt

    def parse_all(self) -> list[LinearProblem]:
        """
        Parsea todos los problemas encontrados en el texto.

        Returns:
            Lista de problemas parseados.
        """
        # Dividir el texto por delimitadores
        sections = self._split_by_delimiter(self.txt)

        problems: list[LinearProblem] = []
        problem_count = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Saltar comentarios al inicio
            lines = section.splitlines()
            start_idx = 0
            for j, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    start_idx = j
                    break

            # Reconstruct section from valid lines
            valid_section = '\n'.join(lines[start_idx:]).strip()

            if not valid_section:
                continue

            try:
                problem = LPParser(valid_section).parse()
                problem_count += 1
                problem.name = f"Problema {problem_count}"
                problems.append(problem)
            except LPParseError:
                raise
            except Exception as e:
                raise LPParseError(
                    f"Error al parsear problema {problem_count + 1}: {e}"
                ) from e

        return problems

    def _split_by_delimiter(self, txt: str) -> list[str]:
        """
        Divide el texto usando cualquier delimitador reconocido.

        Args:
            txt: Texto a dividir.

        Returns:
            Lista de secciones.
        """
        import re

        # Crear patrón regex para cualquier delimitador
        pattern = r'(?:---+|===+|___+)\s*\n'

        # Dividir por el patrón
        sections = re.split(pattern, txt)

        # Filtrar secciones vacías y limpiar
        return [s.strip() for s in sections if s.strip()]

    @staticmethod
    def count_problems(txt: str) -> int:
        """
        Cuenta el número de problemas en el texto.

        Args:
            txt: Texto a analizar.

        Returns:
            Número de problemas encontrados.
        """
        # Contar secciones sin parsear (más rápido)
        normalized = txt
        for delim in ['---', '===', '___']:
            normalized = normalized.replace(delim, '|||MULTI_SEP|||')
        sections = normalized.split('|||MULTI_SEP|||')
        # Contar solo las secciones que parecen tener contenido de problema
        count = 0
        for section in sections:
            section = section.strip()
            if not section:
                continue
            # Skip lines that are only comments
            lines = [ln.strip() for ln in section.splitlines() if ln.strip()]
            # Filter out comment-only lines
            content_lines = [ln for ln in lines if not ln.startswith('#')]
            if content_lines:
                count += 1
        return count
