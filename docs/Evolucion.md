# ISLA LP Benchmark - Evolución del Proyecto

## Estado: Fases 1-5 Completadas ✅

### Roadmap Completado

| Fase | Estado | Descripción |
|------|--------|------------|
| 1. Corrección y estabilización | Terminado | Parser, reportes, modelos de datos |
| 2. Abstracción solvers | Terminado | BaseSolver + SolverRegistry |
| 3. Benchmark orchestrator | Terminado | BenchmarkRunner con warmup, métricas |
| 4. Export/Visualización | Terminado | CSV, JSON, PDF plots, Markdown |
| 5. Reportes y Docs | Terminado | README actualizado |
| 6. Containerization | Terminado | Dockerfile Slim + docker-compose + CI workflow |
| 7. Tests y CI/CD | Terminado | 246 tests, coverage 90%+, ruff lint |
| 8. Logging profesional | Terminado | --log-level, except:pass eliminados |

---

## Historial de Cambios

### v1.5.0 (2026-05-26)

#### MatrixConverter
- Nueva clase `MatrixConverter` con 5 metodos estaticos: `to_highs`, `to_glpk`, `to_cvxopt`, `to_osqp`, `to_scipy`
- Solvers HiGHS, GLPK, CVXOPT, OSQP refactorizados para delegar conversion de matrices a `MatrixConverter`
- 31 tests para MatrixConverter (277 tests total)

#### Analisis de Sensibilidad Real
- Nuevo modulo `src/analysis/sensitivity.py` con `SensitivityAnalysis`
- Extractores nativos: `extract_highs_sensitivity()` (via `hp.getRanging()`), `extract_glpk_sensitivity()` (via API nativa), `extract_gurobi_sensitivity()` (via `getAttr`)
- `SensitivityRange` dataclass con rangos objetivo, RHS, precios sombra y costos reducidos

#### Reportes PDF
- Tablas numericas de sensibilidad en `LPAnalysis`: rangos objetivo, RHS y limites
- Seccion de sensibilidad en `MultiLPAnalysis` por problema

#### Limpieza de Codigo
- 89 errores de ruff corregidos (E722, E741, F401, F541, F841) en 25 archivos
- `ruff check src/ tests/` produce 0 errores

### v1.4.0 (2026-05-26)

#### Infraestructura Docker
- Migracion de `python:3.14-alpine` a `python:3.12-slim` con `coinor-cbc` preinstalado
- `docker-compose.yml` simplificado con servicios `isla-lp`, `solve`, `benchmark`, `list-solvers`
- Variable de entorno `GRB_LICENSE_FILE` para licencias comerciales
- Workflow CI/CD de Docker (build + push a ghcr.io)

#### CLI y Entrypoint
- Entrypoint `isla` registrado en `pyproject.toml` (`[project.scripts]`)
- Version del proyecto actualizada a 1.4.0

### v1.3.0 (2026-05-26)

#### Correcciones Criticas
- Hotfixes: NameError en benchmark.py, imports rotos a sensitivity, exporter.py, validation.py
- CI pipeline actualizado: matriz Python 3.12-3.13, `--cov-fail-under=90`
- `gurobipy` agregado a requirements.txt

#### Refactorizacion y Mejoras
- Eliminados 18+ bloques `except: pass` reemplazados con logging profesional via `get_logger()`
- Flag `--log-level` con soporte DEBUG/INFO/WARNING/ERROR/CRITICAL
- Acceso a duales en HiGHS corregido (eliminada redundancia, agregada guarda de indice)
- `casadi` movido a dependencias opcionales (`pip install isla-lp-benchmark[ipopt]`)
- Semicolons `;` soportados como terminadores de linea en el parser LP

#### Tests
- Suite expandida de 10 a 246 tests. Coverage: core ~100%, parser ~92%

### v1.2.0 (2026-05-13)

#### Nuevas Funcionalidades
- 10 nuevos solvers implementados: ECOS, OSQP, CVXOPT, SCS, Ipopt
- Total de 10 solvers disponibles con registro dinamico via SolverRegistry
- Nuevas flags CLI con shortcuts organizados por seccion:
  - `--version` / `-V`: Mostrar version del programa
  - `--json` / `-j`: Salida estructurada en formato JSON
  - `--quiet` / `-q`: Suprimir salida no esencial
  - `--timeout` / `-T`: Limite de tiempo por solver (segundos)
  - `--no-solve` / `-n`: Solo parsear el problema sin resolver
  - Shortcuts: `-l` (--list-solvers), `-a` (--all-solvers), `-S` (--solvers), `-C` (--plot-comparison), `-O` (--output-dir)
- Ayuda del CLI reorganizada en grupos: Informacion, Seleccion de solver, Resolucion, Benchmark, Salida
- Timeout propagado a todos los solvers via SolverConfig.time_limit + BenchmarkConfig.time_limit
- Diagnostico --no-solve con informacion de variables, restricciones y matriz Polars
- Cobertura completa de 11 solvers con manejo graceful de errores de importacion

#### Nuevos Solvers
- **ECOS** (`ecos`): Solver conico embebido de punto interior para LP y SOCP
- **OSQP** (`osqp`): Solver de optimizacion cuadratica basado en ADMM
- **CVXOPT** (`cvxopt`): Solver de programacion convexa para LP, QP y SOCP
- **SCS** (`scs`): Solver conico de punto fijo escalable (ADMM)
- **Ipopt** (`casadi`): Solver de punto interior para optimizacion no lineal

#### CLI
- Ayuda reorganizada con argumentos agrupados por seccion
- Nuevo formateador personalizado: muestra valores por defecto automaticamente
- Tabla de solvers alineada con contador de disponibilidad
- Shortcuts para todas las flags de uso frecuente

#### Documentacion
- README actualizado a v1.2.0 con changelog completo
- Tablas de solvers, dependencias y flags actualizadas
- Diagramas de arquitectura extendidos con nuevos solvers

### v1.0.0 (2026-04-23)

#### Nuevas Funcionalidades
- Plataforma de benchmark multi-solver
- Solvers implementados:
  - HiGHS (highspy) - nativo
  - GLPK (swiglpk) - nativo
  - CBC (PuLP)
  - Gurobi
- Métricas: tiempo, iteraciones, memoria, nodos
- Warmup para fair benchmarking
- Reportes PDF con gráficos comparativos
- CLI: `--list-solvers`, `--benchmark`, `--solvers`
- Exportación: CSV, JSON, Markdown

#### Limpieza
- Removido duplicado `src/cli.py`
- Actualizado README completo
- Nuevo nombre: ISLA LP Benchmark

#### Docker
- Dockerfile Alpine Python 3.14
- docker-compose.yml

## 1. Introducción

El presente documento describe la evolución del software *Gurobipy-Simplex-General-Solver* (versión 1.0.0) hacia una plataforma orientada al benchmarking de múltiples motores de optimización (solvers), enfocada inicialmente en problemas de Programación Lineal (LP), con proyección futura hacia otros tipos de problemas de optimización.

El objetivo principal de esta transición es transformar una herramienta de resolución individual en un entorno experimental controlado que permita comparar el desempeño de diferentes solvers bajo condiciones homogéneas, aportando valor tanto académico como práctico.

---

## 2. Planteamiento del Problema

Actualmente, el software implementado permite la resolución de problemas de programación lineal mediante el solver Gurobi, incorporando funcionalidades como el parsing de modelos, generación de reportes y soporte multi-problema.

Sin embargo, su enfoque está limitado a la resolución individual de instancias, lo cual restringe su uso en contextos de análisis comparativo. En el ámbito académico y de investigación, resulta fundamental contar con herramientas que permitan evaluar el comportamiento de distintos solvers frente a un mismo conjunto de problemas, considerando métricas de rendimiento, estabilidad y precisión.

En este contexto, se propone extender el sistema hacia un enfoque multi-engine que permita ejecutar múltiples solvers sobre uno o varios problemas, recolectar métricas relevantes y generar análisis comparativos estructurados.

---

## 3. Justificación

Tras la revisión del estado del arte, no se identifican herramientas accesibles, modulares y orientadas al análisis académico que integren múltiples solvers en un entorno de benchmarking controlado con generación automatizada de reportes.

El desarrollo de esta plataforma representa una oportunidad significativa para:

* Facilitar estudios comparativos entre solvers.
* Proveer un punto de entrada unificado para la resolución de problemas de optimización.
* Apoyar procesos de enseñanza en cursos de optimización matemática.
* Generar evidencia empírica sobre el comportamiento de algoritmos en distintos escenarios.

---

## 4. Estado Actual del Sistema

El sistema en su versión actual cuenta con las siguientes funcionalidades:

* Parsing de problemas de optimización.
* Integración con el solver Gurobi.
* Generación de reportes ejecutivos en formato PDF.
* Soporte para la resolución de múltiples problemas.
* Configuración básica del solver.
* Arquitectura modular con bajo acoplamiento entre componentes.

---

## 5. Propuesta de Evolución

La transición hacia un sistema de benchmarking requiere la implementación de mejoras estructurales, correcciones y nuevas funcionalidades, organizadas en las siguientes categorías:

### 5.1 Correcciones

Se identifican aspectos que requieren ajuste para garantizar la estabilidad y confiabilidad del sistema:

* Corrección de la generación de gráficas de regiones factibles.
* Validación y robustecimiento del parsing de archivos en formato `.lp`.
* Ajuste y mejora de los reportes en PDF.
* Revisión y validación de los modelos de datos existentes.

---

### 5.2 Modificaciones

Se plantean cambios en la estructura actual del sistema para facilitar su evolución:

* Rediseño del mecanismo de generación y entrega de reportes.
* Adaptación de los modelos de datos hacia una representación agnóstica respecto al solver.

---

### 5.3 Refactorización

Con el fin de mejorar la mantenibilidad y escalabilidad del sistema, se propone:

* Reestructuración del CLI como un módulo independiente.
* Definición de una abstracción base para los solvers (Base Solver).
* Refactorización del solver actual (Gurobi) para alinearlo con la nueva abstracción.
* Reorganización de los módulos de generación de reportes.
* Mejora del sistema de ayuda y documentación del CLI.

---

### 5.4 Adiciones

Las siguientes funcionalidades constituyen el núcleo del nuevo sistema:

* Implementación de adaptadores para la integración de múltiples solvers.

* Desarrollo de un orquestador de benchmarking con las siguientes capacidades:

  * Recepción de múltiples problemas y solvers.
  * Ejecución repetida de experimentos.
  * Medición de métricas como tiempo de ejecución, número de iteraciones, estado de solución y valor objetivo.
  * Almacenamiento estructurado de resultados (DataFrame).
  * Detección de discrepancias entre resultados de distintos solvers.

* Incorporación de nuevas opciones en el CLI:

  * `--solvers`
  * `--repetitions`
  * `--output-csv`
  * `--plot-comparison`
  * `--time-limit`

* Implementación de un handler específico para el modo benchmark.

* Extensión de los reportes PDF para incluir análisis comparativos.

* Exportación de resultados en formatos estructurados (e.g., CSV).

* Contenerización del sistema mediante Docker.

---

### 5.5 Metodología de Benchmark

Se propone formalizar el proceso experimental mediante:

* Definición de métricas de evaluación:

  * Tiempo de ejecución
  * Iteraciones
  * Valor objetivo
  * Estado de solución
  * Consumo de recursos (opcional)

* Establecimiento de condiciones controladas:

  * Número de repeticiones por experimento
  * Configuración uniforme de parámetros
  * Control de variabilidad del entorno

* Definición de criterios de comparación:

  * Tolerancias numéricas
  * Consistencia de resultados
  * Identificación de outliers

---

### 5.6 Reproducibilidad

Para garantizar la validez académica del sistema, se recomienda incluir:

* Registro de versiones de software y dependencias.
* Especificación del entorno de ejecución.
* Documentación de configuraciones experimentales.
* Uso de contenedores para replicabilidad.

---

## 6. Documentación

La documentación del sistema deberá actualizarse de manera integral, incluyendo:

* README del proyecto.
* Manuales dirigidos a distintos perfiles:

  * Estudiantes
  * Desarrolladores
  * Usuarios con enfoque matemático
* Guía de contribución al proyecto.

---

## 7. Mantenibilidad

La evolución del sistema deberá priorizar:

* Bajo acoplamiento entre módulos.
* Separación clara de responsabilidades.
* Escalabilidad para la integración de nuevos solvers.
* Mantenibilidad del código mediante buenas prácticas de diseño.

Se propone inicialmente consolidar la funcionalidad y el rendimiento del sistema, para posteriormente incorporar métricas de calidad, trazabilidad y monitoreo.

---

## 8. Roadmap Propuesto

Se sugiere estructurar el desarrollo en las siguientes fases:

1. Corrección y estabilización del sistema actual.
2. Definición e implementación de la abstracción de solvers.
3. Desarrollo del orquestador de benchmarking.
4. Implementación de exportación y visualización de resultados.
5. Mejora de reportes y documentación.
6. Contenerización y preparación para despliegue.
