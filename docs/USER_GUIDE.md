# Guia de Usuario - ISLA LP Benchmark v1.8.1


Esta guia es para **usuarios finales** que quieren resolver y comparar problemas de Programacion Lineal.

## Que es Este Proyecto?

ISLA LP Benchmark es una plataforma de benchmarking que permite:
- Resolver problemas de Programacion Lineal (PL) y MILP
- Comparar multiples solvers (15 motores de optimizacion)
- Generar metricas y reportes comparativos en PDF, CSV, JSON y HTML

## Inicio Rapido

### 1. Instalar Dependencias

```bash
# Usando Poetry (recomendado)
poetry install

# Usando pip
pip install -r requirements.txt
pip install -e .
```

### 2. Listar Solvers Disponibles

```bash
python -m src.cli --list-solvers
# o usando shortcut:
python -m src.cli -l
```

### 3. Resolver un Problema

```bash
# Formato LP (estandar)
python -m src.cli problema.txt
# Formato MPS (estandar industrial)
python -m src.cli problema.mps
```

### 4. Ejecutar Benchmark

```bash
python -m src.cli -b -S gurobi cbc -r 3 problema.txt
```

## Modo Benchmark

### Ejecucion Basica

```bash
# Benchmark con solvers especificos
python -m src.cli -b -S gurobi cbc -r 3 problema.txt

# Con todos los solvers disponibles
python -m src.cli -b -a problema.txt

# Con graficos comparativos
python -m src.cli -b -S gurobi cbc -C problema.txt

# Con limite de tiempo
python -m src.cli -b -a -T 30 problema.txt
```

### Flags de Benchmark

| Flag | Alias | Descripcion |
|------|-------|------------|
| `--benchmark` | `-b` | Activa modo benchmark |
| `--solvers` | `-S` | Lista de solvers a usar (ej: `-S gurobi cbc`) |
| `--all-solvers` | `-a` | Usar todos los solvers disponibles |
| `--repetitions` | `-r` | Numero de repeticiones |
| `--timeout` | `-T` | Limite de tiempo por solver (segundos) |
| `--plot-comparison` | `-C` | Generar graficos comparativos |
| `--output-csv` | | Exportar resultados a CSV |
| `--output-dir` | `-O` | Directorio de salida |
| `--pdf` | `-p` | Generar reporte PDF |
| `--quiet` | `-q` | Suprimir salida no esencial |
| `--log-level` | | Nivel de log: DEBUG/INFO/WARNING/ERROR/CRITICAL |

### Ejemplo de Salida

```
============================================================
BENCHMARK SUMMARY
============================================================
Total de pruebas: 6
Exitosas: 6
Fallidas: 0

Por Solver:
------------------------------------------------------------
Solver          Runs     Exitosos   Tiempo Promedio
------------------------------------------------------------
gurobi          3        3          16.12ms
cbc             3        3          111.32ms
============================================================
```

## Solvers Disponibles

| Solver | Paquete | API | Disponibilidad |
|--------|---------|-----|---------------|
| Gurobi | gurobipy | Wrapper | Requiere licencia |
| HiGHS | highspy | Native | Requiere instalacion |
| GLPK | swiglpk | Native | Requiere instalacion |
| CBC | pulp | Wrapper | Siempre disponible |
| SCIP | pyscipopt | Native | Requiere instalacion |
| ECOS | ecos | Native | Requiere instalacion |
| OSQP | osqp | Native | Requiere instalacion |
| CVXOPT | cvxopt | Native | Requiere instalacion |
| SCS | scs | Native | Requiere instalacion |
| Ipopt | casadi | Native | Pip installable |

**Nota**: Gurobi, SCIP, CBC, ECOS, OSQP, CVXOPT y SCS soportan MILP (variables enteras y binarias).

## Resolucion Simple

### 1. Crear Archivo de Problema

```lp
max: 3000x + 5000y

2x + 3y <= 120
x + 3y <= 90

x >= 0
y >= 0
```

### 2. Ejecutar

```bash
python -m src.cli problema.txt
```

### 3. Resultados

```
Optimal value: 190000.00
x = 30.00
y = 20.00
```

### Salida JSON

```bash
python -m src.cli problema.txt --json
```

Salida:
```json
{
  "solver": "gurobi",
  "status": "OPTIMAL",
  "objective_value": 190000.0,
  "variables": {"x": 30.0, "y": 20.0},
  "times": {"parse_ms": 1.0, "build_ms": 8.6, "solve_ms": 22.6, "total_ms": 32.8}
}
```

### Solo Parsear (Diagnostico)

```bash
python -m src.cli problema.txt --no-solve
```

Salida:
```
  Problema: problema.txt
  Variables: 2
  Restricciones: 2
  Tipo: max
  Matriz: 2x2 (Polars LP)
  Variables: x, y
```

## Modo REPL Interactivo

El sistema incluye un modo interactivo para explorar problemas y probar solvers sin salir de la terminal.

```bash
python -m src.cli --repl
```

**Comandos principales:**
- `load <archivo>`: Carga un problema LP.
- `load-mps <archivo>`: Carga un problema MPS.
- `info`: Muestra dimensiones y sentido del problema.
- `solve <solver>`: Resuelve el problema cargado.
- `vars`: Lista variables y sus limites.
- `export <archivo>`: Exporta el problema actual a formato LP.
- `solvers`: Lista motores disponibles.
- `help`: Muestra ayuda.
- `quit`: Sale del REPL.

---

## Formato de Problemas

### Funcion Objetivo

```
max: 3000x + 5000y
min: 2x + 3y + 5z
```

### Restricciones

```
x + y <= 100
2x + 3y >= 50
x + y = 75
```

### Limites de Variables

```
x >= 0         # limite inferior
y <= 50        # limite superior
x free         # sin limites
0 <= x <= 100  # ambos limites
```

### Variables Enteras y Binarias (MILP)

```
x int          # Variable entera
y binary       # Variable binaria (0 o 1)
z integer      # Equivalente a int
w bin          # Equivalente a binary
```

### Multiples Problemas

```
max: x + 2y
x + y <= 10
x >= 0; y >= 0

---

min: 3x + y
x - y >= 5
x >= 0; y >= 0
```

## Opciones CLI

### Resolucion Simple

| Opcion | Alias | Descripcion |
|--------|-------|-------------|
| `--solver` | `-s` | Solver a usar |
| `--multi` | `-m` | Modo multi-problema |
| `--visualize` | `-v` | Generar grafico 2D |
| `--pdf` | `-p` | Generar informe PDF |
| `--times` | `-t` | Mostrar tiempos de ejecucion |
| `--json` | `-j` | Salida estructurada JSON |
| `--no-solve` | `-n` | Solo parsear sin resolver |
| `--timeout` | `-T` | Limite de tiempo por solver (seg) |
| `--quiet` | `-q` | Suprimir salida no esencial |
| `--verbose` | | Salida detallada |
| `--output` | `-o` | Ruta de salida para archivos |
| `--log-level` | | Nivel de log: DEBUG/INFO/WARNING/ERROR/CRITICAL |

### Informacion

| Opcion | Alias | Descripcion |
|--------|-------|-------------|
| `--list-solvers` | `-l` | Listar solvers disponibles |
| `--version` | `-V` | Mostrar version del programa |

### Comandos de Ejemplo

```bash
# Resolver con solver especifico
python -m src.cli problema.txt -s cbc

# Con grafico + PDF + tiempos
python -m src.cli problema.txt -v -p -t

# Salida JSON
python -m src.cli problema.txt -j

# Con limite de tiempo
python -m src.cli problema.txt -T 30

# Diagnostico (solo parsear)
python -m src.cli problema.txt -n

# Modo silencioso (solo resultado)
python -m src.cli problema.txt -q

# Version
python -m src.cli --version
```

## Multiples Problemas

El sistema soporta resolver multiples problemas desde un solo archivo usando delimitadores (`---`, `===`, `___`).

### Archivo Multi-Problema
```
max: x + 2y
x + y <= 10
x >= 0; y >= 0

---

min: 3x + y
x - y >= 5
x >= 0; y >= 0
```

### Comandos Multi-Problema
```bash
# Resolver multiples problemas
python -m src.cli problema.txt -m

# Multi-problema con PDF
python -m src.cli problema.txt -m -p
```

### Reporte Multi-Problema
El reporte incluye:
1. **Portada** con estadisticas generales
2. **Resumen ejecutivo** con tabla de resultados
3. **Pagina individual** por problema (funcion objetivo, restricciones, solucion, holguras, grafico)
4. **Resumen de tiempos** por problema

## Soporta Formatos Estándar de Industria (MPS)

El sistema soporta el formato MPS (Mathematical Programming System), un estándar de la industria para intercambio de problemas de optimización lineal y mixta-enteros.

### Características del formato MPS Soportadas
- Formato fijo y libre
- Marcadores INTORG/INTEND para variables enteras
- Secciones: NAME, ROWS, COLUMNS, RHS, BOUNDS, RANGES, QSECTION
- Comentarios con `*` en columna 1

### Uso básico
```bash
# Resolver problema en formato MPS
python -m src.cli problema.mps

# Resolver MPS con opciones adicionales
python -m src.cli problema.mps --solver gurobi --pdf --visualize
```

### Ejemplo de archivo MPS sencillo
```
NAME          TESTPROB
ROWS
 N  COST
 L  LIM1
 L  LIM2
COLUMNS
    X1       COST        1.0   LIM1        1.0
    X1       LIM2        1.0
    X2       COST        2.0   LIM1        1.0
    X2       LIM2        1.0
RHS
    RHS      LIM1        5.0
    RHS      LIM2        3.0
BOUNDS
 UP B1       X1        4.0
 LO B2       X2        0.0
 ENDATA
```

## Generador de Problemas Sintéticos

El sistema incluye un generador de problemas sintéticos útil para testing, benchmarks y experimentos.

### Uso desde línea de comandos
```bash
# Generar y resolver un problema aleatorio LP
python -m src.cli --generate-problem --vars 10 --constraints 5 --density 0.3

# Generar problema MILP y resolverlo
python -m src.cli --generate-problem --vars 8 --constraints 4 --int-vars 3 --solver gurobi

# Guardar problema generado en archivo
python -m src.cli --generate-problem --vars 15 --constraints 10 --output problem_generated.lp
```

### Parámetros disponibles
| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--vars` | Número de variables | 5 |
| `--constraints` | Número de restricciones | 3 |
| `--density` | Densidad de la matriz (0-1) | 0.3 |
| `--int-vars` | Número de variables enteras (para MILP) | 0 |
| `--coeff-range` | Rango de coeficientes "min,max" | "-10,10" |
| `--rhs-range` | Rango de lados derechos "min,max" | "-100,100" |
| `--output` | Archivo donde guardar el problema generado | None (solo resuelve) |
| `--solver` | Solver a usar para resolver el problema generado | "gurobi" |

### Uso programático
```python
from src.utils.problem_generator import ProblemGenerator

# Generar problema LP aleatorio
gen = ProblemGenerator(seed=42)
problem = gen.generate_lp(n_vars=20, n_constraints=10, density=0.25)

# Generar problema MILP
mip_problem = gen.generate_milp(n_vars=15, n_constraints=8, n_int_vars=5)

# Generar problema mal condicionado para stress testing
ill_problem = gen.generate_ill_conditioned()

# Exportar a formato LP o MPS
lp_text = problem.to_lp()
mps_text = problem.to_mps()
```

## MILP (Programacion Lineal Entera)

El sistema soporta variables enteras (`int`, `integer`) y binarias (`bin`, `binary`).

### Ejemplo MILP
```
max: 3000x + 5000y

2x + 3y <= 120
x + 3y <= 90

x int          # Variable entera
y binary       # Variable binaria (0 o 1)

x >= 0; y >= 0
```

### Solvers con soporte MILP
Gurobi, CBC, SCIP, ECOS, CVXOPT

```bash
# Resolver MILP con Gurobi
python -m src.cli problema_milp.txt -s gurobi

# Resolver MILP con CBC
python -m src.cli problema_milp.txt -s cbc
```

---

## Entendiendo los Resultados

### Solucion Optima

```
Status: OPTIMAL
Optimal value: 190000.00
x = 30.00
y = 20.00
```

### Problema Infactible

```
Status: INFEASIBLE
```

Significa que las restricciones se contradicen entre si.

### Problema No Acotado

```
Status: UNBOUNDED
```

El objetivo puede mejorar indefinidamente.

## Reporte PDF Benchmark

El reporte incluye:

1. **Portada**: Informacion del benchmark
2. **Resumen Estadistico**: Tabla comparativa por solver
3. **Comparacion por Solver**: Stats detallados por solver
4. **Resultados Detallados**: Tabla completa con todos los resultados
5. **Definiciones de Problemas**: Texto original de cada problema
6. **Graficos**:
   - Tiempo de ejecucion
   - Tasa de exito
   - Uso de memoria
   - Perfiles de rendimiento (Dolan-More)
7. **Analisis de Escalabilidad**: Relacion tamano vs tiempo
8. **Matriz de Correlacion**: Correlacion entre metricas
9. **Analisis Estadistico**: Test de Friedman, post-hoc Nemenyi, ANOVA
10. **Recomendaciones**: Sugerencias basadas en resultados

## Solucion de Problemas

### "Solver no disponible"

- Verificar instalacion: `python -m src.cli -l`
- Instalar solver: `pip install ecos` o `pip install osqp`

### "Problema infactible"

- Verificar restricciones contradictorias
- Revisar coeficientes

### Resultados incorrectos

- Verificar coeficientes
- Verificar direcciones de restricciones
- Comparar con otro solver usando `-b -S solver1 solver2`

---

Para detalles tecnicos, ver [README.md](../README.md).
