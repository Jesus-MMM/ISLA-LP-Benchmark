# Guia del Desarrollador - ISLA LP Benchmark v1.4.0

Esta guia es para **desarrolladores** que quieren extender o integrar el proyecto.

## Arquitectura del Sistema

```
src/
├── cli/                      # Interfaz CLI
│   ├── __main__.py           # Punto de entrada con parser organizado
│   ├── benchmark.py          # Handler benchmark
│   ├── solve.py              # Handler resolucion
│   └── __init__.py           # Utilidades sistema
├── solver/                   # 15 implementaciones de solvers
│   ├── base.py               # BaseSolver, SolverRegistry, SolverStats
│   ├── gurobi.py             # GurobiSolver (gurobipy)
│   ├── highs_solver.py       # HiGHSSolver (highspy)
│   ├── glpk_solver.py        # GLPKSolver (swiglpk)
│   ├── cbc.py                # CBCSolver (PuLP)
│   ├── scip.py               # SCIPSolver (PySCIPOpt)
│   ├── ecos.py               # ECOSSolver (ecos)
│   ├── osqp_solver.py        # OSQPSolver (osqp)
│   ├── cvxopt_solver.py      # CVXOPTSolver (cvxopt)
│   ├── scs_solver.py         # SCSSolver (scs)
│   ├── ipopt_solver.py       # IpoptSolver (casadi)
│   ├── benchmark.py          # BenchmarkRunner, BenchmarkConfig
│   ├── multi_solver.py       # MultiSolverResult
│   └── __init__.py           # Registro de todos los solvers
├── analysis/                 # Analisis y reportes
│   ├── analysis.py           # LPAnalysis - reporte single
│   ├── benchmark_report.py   # BenchmarkReport - PDF benchmark
│   ├── benchmark_results.py  # ResultsExporter, export_benchmark_results
│   ├── multi_analysis.py     # MultiLPAnalysis - reporte multi-problema
│   └── __init__.py
├── parser/                   # Parsing de archivos
│   ├── lp_parser.py          # LPParser - formato texto propio
│   ├── cplex_parser.py       # CPLEXParser - formato CPLEX/LP
│   ├── multi_parser.py       # MultiLPParser - multi-problema
│   └── __init__.py
├── core/                     # Modelos de datos
│   ├── problem.py            # LinearProblem
│   ├── constraint.py         # LinearConstraint
│   ├── bound.py              # VariableBound
│   ├── solution.py           # Solution
│   ├── exceptions.py         # LPError y subclases
│   ├── constants.py          # Constantes centralizadas
│   ├── verification.py       # verify_solution, compare_solutions
│   └── __init__.py
├── matrix/                   # Construccion Polars
│   ├── builder.py            # LPBuilder
│   ├── matrix.py             # PolarsLP
│   └── __init__.py
├── visualization/            # Graficos 2D
│   ├── visualization.py      # LinearVisualization
│   └── __init__.py
└── utils/                    # Utilidades
    ├── validation.py         # LPValidator
    ├── exporter.py           # LPExporter
    ├── logging.py            # ExecutionTimes
    └── __init__.py
```

## Uso Basico

### Resolver un Problema

```python
from src.parser import LPParser
from src.matrix import LPBuilder
from src.solver import SolverRegistry, SolverConfig

# Parsear
problem = LPParser(texto).parse()

# Construir
lp = LPBuilder(problem).build()

# Obtener solver con configuracion
solver_class = SolverRegistry.get('cbc')
config = SolverConfig(verbose=False, time_limit=30.0)
solver = solver_class(problem, config)

# Resolver
solution = solver.solve()

# Resultados
print(solution.objective_value)
print(solution.variables)
```

### Modo Benchmark

```python
from src.solver import BenchmarkRunner, BenchmarkConfig

config = BenchmarkConfig(
    warmup_runs=1,
    runs_per_problem=3,
    verbose=False,
    collect_memory=True,
    time_limit=30.0,  # Timeout para cada solver
)

runner = BenchmarkRunner(config)
problems = [("problema1", texto)]
solvers = ['gurobi', 'cbc', 'scip']

results = runner.run(problems, solvers)

# Metricas
summary = runner.get_summary()
print(summary['by_solver'])
```

### Listar Solvers Disponibles

```python
from src.solver import SolverRegistry

# Lista de nombres
solvers = SolverRegistry.list_solvers()
print(solvers)  # ['gurobi', 'highs', 'glpk', 'cbc', 'scip', 'ecos', ...]

# Solo disponibles
available = SolverRegistry.list_solvers(available_only=True)
print(available)  # Solvers que se pueden usar ahora

# Informacion detallada
all_info = SolverRegistry.list_all_info()
for name, info in all_info.items():
    status = "DISPONIBLE" if info['available'] else "NO DISPONIBLE"
    error = f" - {info['error']}" if info['error'] else ""
    print(f"  {name:<20s}{status}{error}")
```

## Registro de Solvers

### Usando @register_solver Decorator

```python
from src.solver import BaseSolver, SolverStats, SolverRegistry, register_solver
from src.core import Solution, LinearProblem

@register_solver("mi_solver")
class MiSolver(BaseSolver):
    """Implementacion de solver personalizado."""

    def __init__(self, model: LinearProblem, config=None):
        super().__init__(config)
        self.model = model
        self._solution = None

    @property
    def solver_name(self) -> str:
        return "mi_solver"

    @property
    def solver_version(self) -> str:
        return "1.0.0"

    @property
    def is_available(self) -> bool:
        return True

    def solve(self) -> Solution:
        # Resolver problema
        return Solution(
            status="OPTIMAL",
            objective_value=42.0,
            variables={"x": 1.0, "y": 2.0}
        )

    def get_stats(self) -> SolverStats:
        return SolverStats(iterations=2, nodes=0)
```

### Patron de Importacion con Graceful Degradation

Cada solver sigue este patron para manejar dependencias faltantes:

```python
try:
    import ecos
except ImportError:
    ecos = None  # El solver se registra como NO DISPONIBLE

@register_solver("ecos")
class ECOSSolver(BaseSolver):
    @property
    def is_available(self) -> bool:
        return ecos is not None

    def solve(self) -> Solution:
        if ecos is None:
            return Solution(status="ERROR: ecos module not available", ...)
        # ...
```

### Verificar Disponibilidad de SCIP

```python
from src.solver import SolverRegistry

info = SolverRegistry.list_all_info()
print(info.get('scip', {}).get('available', False))
```

## APIs Principales

### LinearProblem

```python
from src.core import LinearProblem, LinearConstraint, VariableBound

problem = LinearProblem(
    objective={"x": 3000, "y": 5000},
    sense="max",
    constraints=[
        LinearConstraint(
            coefficients={"x": 2, "y": 3},
            rhs=120,
            sense="<="
        )
    ],
    bounds={
        "x": VariableBound("x", 0, None),
        "y": VariableBound("y", 0, None)
    }
)
```

### Solution

```python
solution = Solution(
    status="OPTIMAL",
    objective_value=190000.0,
    variables={"x": 30.0, "y": 20.0},
    dual_values={"c1": 1000.0},
    reduced_costs={"x": 0.0, "y": 0.0}
)

# Verificar estado
solution.is_optimal()    # True
solution.is_infeasible() # False
solution.is_unbounded()  # False
```

### SolverConfig

```python
from src.solver import SolverConfig

config = SolverConfig(
    verbose=False,
    time_limit=30.0,     # Timeout en segundos
    mip_gap=0.01,        # Gap MIP (1%)
    threads=4,           # Hilos paralelos
    presolve=1,          # Presolve automatico
    seed=42,             # Semilla aleatoria
)
```

### BenchmarkRunner

```python
runner = BenchmarkRunner(config)

# Agregar resultado
runner.results.append(BenchmarkResult(
    solver_name="cbc",
    problem_name="problema1",
    problem_text=texto,
    solution=solution,
    stats=SolverStats(iterations=2, nodes=0),
    parse_time=0.001,
    build_time=0.002,
    solve_time=0.045,
    total_time=0.048,
    memory_used_mb=45.2,
    peak_memory_mb=52.1
))

# Exportar
runner.export_csv(Path("results.csv"))
runner.export_json(Path("results.json"))
```

## Verificacion de Soluciones

### verify_solution()

```python
from src.core.verification import verify_solution, compare_solutions
from src.core import LinearProblem, Solution

# Verificar una solucion
is_valid, issues = verify_solution(problem, solution)
if not is_valid:
    print("Problemas encontrados:")
    for issue in issues:
        print(f"  - {issue}")

# Comparar soluciones de multiples solvers
solutions = [gurobi_sol, cbc_sol, scip_sol]
warnings = compare_solutions(problem, solutions)
for warning in warnings:
    print(f"ADVERTENCIA: {warning}")
```

**Tolerancias**: Usa `FEASIBILITY_TOLERANCE` (1e-6) por defecto.

## Exportacion Avanzada

### ResultsExporter

```python
from src.analysis.benchmark_results import ResultsExporter, export_benchmark_results
from pathlib import Path

# Usando ResultsExporter
exporter = ResultsExporter(runner)
exporter.to_markdown(Path("report.md"))
exporter.to_html(Path("report.html"), include_plots=True, plots_dir=Path("plots"))

# Metodo rapido (recomendado)
paths = export_benchmark_results(
    runner=runner,
    output_dir=Path("data/benchmark_output"),
    formats=["json", "csv", "md", "html"],
    include_plots=True
)
# Retorna: {"json": Path(...), "csv": Path(...), "md": Path(...), "html": Path(...)}
```

## Analisis Multi-Problema

### MultiLPAnalysis

```python
from src.analysis.multi_analysis import MultiLPAnalysis
from src.solver import MultiSolverResult

analysis = MultiLPAnalysis(results)
analysis.generate_pdf("output/multi_report.pdf")
```

**Secciones del reporte**:
1. Portada con estadisticas
2. Resumen ejecutivo
3. Pagina individual por problema
4. Resumen de tiempos

---

## Extensiones

### Agregar Nuevo Solver

1. Crear archivo en `src/solver/mi_solver.py`
2. Implementar clase que hereda de `BaseSolver`
3. Usar decorador `@register_solver("mi_solver")`
4. Agregar import en `src/solver/__init__.py` con try/except
5. Agregar dependencia en `pyproject.toml`

```python
# src/solver/mi_solver.py
from src.solver import BaseSolver, SolverStats, register_solver
from src.core import Solution
from src.matrix import PolarsLP

try:
    import mi_paquete
except ImportError:
    mi_paquete = None

@register_solver("mi_solver")
class MiSolver(BaseSolver):
    @property
    def solver_name(self) -> str:
        return "mi_solver"

    @property
    def is_available(self) -> bool:
        return mi_paquete is not None

    def solve(self) -> Solution:
        if mi_paquete is None:
            return Solution(status="ERROR: mi_paquete not available", ...)
        # Logica de resolucion
```

### Agregar Nuevo Parser

```python
# src/parser/mi_parser.py
from ..core import LinearProblem

class MiParser:
    def __init__(self, texto: str):
        self.texto = texto

    def parse(self) -> LinearProblem:
        # Logica de parsing
        return LinearProblem(...)
```

### Agregar Visualizacion

```python
from src.analysis.benchmark_results import BenchmarkVisualizer

viz = BenchmarkVisualizer(runner)
viz.plot_times_comparison(save_path="times.png")
viz.plot_memory_comparison(save_path="memory.png")
```

## Sistema de Logging

El proyecto usa Python logging con nivel configurable via CLI (`--log-level`).

### Configuracion por Defecto

```python
from src.utils.logging import get_logger, set_default_level, LogLevel

# Obtener logger para el modulo actual
logger = get_logger(__name__)

# Cambiar nivel global
set_default_level(LogLevel.DEBUG)

# Uso en el modulo
logger.debug("Mensaje detallado")
logger.info("Proceso completado")
logger.warning("Situacion inesperada")
logger.error("Error recuperable")
```

### Uso en Solvers

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

try:
    resultado = operacion_riesgosa()
except Exception as e:
    logger.debug(f"Error en operacion: {e}")
    # Continuar con valor por defecto
    resultado = None
```

### Buenas Practicas

- Usar `get_logger(__name__)` en cada modulo (sigue la jerarquia del paquete)
- NO usar `print()` ni `except: pass` — reemplazar con `logger.debug()`
- El nivel `--log-level=DEBUG` activa toda la informacion de diagnostico

## Patrones Comunes

### Manejo de Errores

```python
from src.core.exceptions import LPParseError, LPSolverError

try:
    problem = LPParser(texto).parse()
except LPParseError as e:
    print(f"Error de parseo: {e}")
```

### Verificar Solucion

```python
solution = solver.solve()

if solution.is_optimal():
    print(f"Optimo: {solution.objective_value}")
elif solution.is_infeasible():
    print("Problema infactible")
elif solution.is_unbounded():
    print("Problema no acotado")
```

### Iterar SolverRegistry

```python
from src.solver import SolverRegistry

# Probar cada solver disponible
for name in SolverRegistry.list_solvers(available_only=True):
    cls = SolverRegistry.get(name)
    solver = cls(problem)
    sol = solver.solve()
    print(f"{name}: {sol.status} = {sol.objective_value}")
```

---

Para referencia de API completa, ver [README.md](../README.md).
