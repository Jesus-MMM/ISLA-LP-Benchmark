"""
Modulo de analisis para problemas de programacion lineal.
Exporta clases con los nombres que espera el CLI y analisis avanzado.
"""

from .analysis import LPAnalysis, ExecutionTimes
from .multi_analysis import MultiLPAnalysis
from .benchmark_results import (
    ResultsExporter, 
    export_benchmark_results
)
from .benchmark_report import BenchmarkReport

__all__ = [
    "LPAnalysis",
    "MultiLPAnalysis",
    "ExecutionTimes",
    "ResultsExporter",
    "export_benchmark_results",
    "BenchmarkReport"
]
