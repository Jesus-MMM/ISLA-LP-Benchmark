"""
Sistema de cache para problemas y resultados de solver.

Almacena problemas parseados y resultados de solver en
~/.cache/isla-lp-benchmark/ con hash SHA256 y TTL configurable.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import time
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "isla-lp-benchmark"
PARSED_DIR = CACHE_DIR / "parsed"
RESULTS_DIR = CACHE_DIR / "results"
DEFAULT_TTL = 86400  # 24 horas


def _ensure_dirs() -> None:
    """Crea los directorios de cache si no existen."""
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _content_hash(content: str) -> str:
    """Calcula hash SHA256 del contenido."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _is_fresh(path: Path, ttl: int) -> bool:
    """Verifica si un archivo de cache aun es valido segun TTL."""
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < ttl


class ProblemCache:
    """Cachea problemas parseados y resultados de solver.

    Ejemplo:
        cache = ProblemCache()
        problem = cache.get_parsed("texto del problema")
        if problem is None:
            problem = parse(texto)
            cache.set_parsed("texto del problema", problem)

        result = cache.get_result("texto", "highs")
        if result is None:
            result = solver.solve()
            cache.set_result("texto", "highs", result)
    """

    def __init__(self, ttl: int = DEFAULT_TTL):
        """Inicializa el cache con un TTL en segundos.

        Args:
            ttl: Tiempo de vida del cache en segundos. Default: 86400 (24h).
        """
        self.ttl = ttl
        _ensure_dirs()

    def _parsed_path(self, content: str) -> Path:
        content_hash = _content_hash(content)
        return PARSED_DIR / f"{content_hash}.pkl"

    def get_parsed(self, content: str) -> object | None:
        """Obtiene un problema parseado del cache.

        Args:
            content: Texto original del problema.

        Returns:
            El objeto LinearProblem si está en cache y vigente, None en caso contrario.
        """
        path = self._parsed_path(content)
        if not _is_fresh(path, self.ttl):
            return None
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def set_parsed(self, content: str, problem: object) -> None:
        """Almacena un problema parseado en el cache.

        Args:
            content: Texto original del problema.
            problem: Objeto LinearProblem a cachear.
        """
        path = self._parsed_path(content)
        try:
            with open(path, "wb") as f:
                pickle.dump(problem, f)
        except Exception:
            pass

    def _result_path(self, content: str, solver_name: str) -> Path:
        content_hash = _content_hash(content)
        safe_name = solver_name.replace("/", "_").replace("\\", "_")
        return RESULTS_DIR / f"{content_hash}_{safe_name}.json"

    def get_result(self, content: str, solver_name: str) -> dict | None:
        """Obtiene un resultado de solver del cache.

        Args:
            content: Texto original del problema.
            solver_name: Nombre del solver.

        Returns:
            Dict con el resultado si está en cache y vigente, None en caso contrario.
        """
        path = self._result_path(content, solver_name)
        if not _is_fresh(path, self.ttl):
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    def set_result(self, content: str, solver_name: str, result: dict) -> None:
        """Almacena un resultado de solver en el cache.

        Args:
            content: Texto original del problema.
            solver_name: Nombre del solver.
            result: Dict con el resultado a cachear.
        """
        path = self._result_path(content, solver_name)
        try:
            with open(path, "w") as f:
                json.dump(result, f, indent=2, default=str)
        except Exception:
            pass

    def invalidate_all(self) -> None:
        """Invalida todo el cache eliminando los archivos."""
        for d in [PARSED_DIR, RESULTS_DIR]:
            if d.exists():
                for f in d.iterdir():
                    try:
                        f.unlink()
                    except Exception:
                        pass

    def invalidate_parsed(self, content: str) -> None:
        """Invalida el cache de un problema parseado.

        Args:
            content: Texto original del problema.
        """
        path = self._parsed_path(content)
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass

    def get_stats(self) -> dict:
        """Obtiene estadisticas del cache.

        Returns:
            Dict con cantidad de entradas y antigüedad.
        """
        _ensure_dirs()
        parsed_files = list(PARSED_DIR.iterdir()) if PARSED_DIR.exists() else []
        result_files = list(RESULTS_DIR.iterdir()) if RESULTS_DIR.exists() else []
        return {
            "parsed_entries": len(parsed_files),
            "result_entries": len(result_files),
            "cache_dir": str(CACHE_DIR),
        }
