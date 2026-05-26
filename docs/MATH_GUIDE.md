# Guia Matematica - ISLA LP Benchmark v1.4.0

Esta guia es para **matematicos e investigadores** que quieren entender la teoria detras del sistema.

## Fundamento Matematico

### Problema de Programacion Lineal

Un problema de Programacion Lineal (PL) tiene:

1. **Funcion Objetivo**: Maximizar o minimizar
   ```
   max/min: c1x1 + c2x2 + ... + cnxn
   ```

2. **Restricciones**: Desigualdades/igualdades lineales
   ```
   a11x1 + a12x2 + ... + a1nxn <= b1
   a21x1 + a22x2 + ... + a2nxn >= b2
   ...
   am1x1 + am2x2 + ... + amnxn = bm
   ```

3. **Limites**: Limites de variables
   ```
   xi >= li
   xi <= ui
   ```

### Forma Estandar

El sistema convierte problemas a forma estandar:

- **Maximizacion**: Convertir a minimizacion si es necesario
- **Desigualdades**: Convertir >= a <= multiplicando por -1
- **Variables**: Agregar variables de holgura para restricciones <=

## Metodos de Solucion

### Simplex

El **Metodo Simplex** (Dantzig, 1947) es el algoritmo primario:

1. **Solucion Factible Basica**: Comenzar en un vertice de la region factible
2. **Operaciones Pivote**: Moverse a vertices adyacentes con mejor valor objetivo
3. **Prueba de Optimalidad**: Detenerse cuando ningun vertice adyacente mejore el objetivo

**Complejidad**: O(mn) por iteracion, polinomial en promedio.

### Punto Interior

Los **Metodos de Barrera** (Karmarkar, 1984) siguen el camino central:

1. **Barrera Logaritmica**: Agregar termino de barrera al objetivo
2. **Camino Central**: Seguir camino al optimo
3. **Metodo de Newton**: Resolver condiciones KKT

### ADMM (Alternating Direction Method of Multipliers)

Usado por OSQP y SCS para problemas convexos a gran escala:
1. Descomponer el problema en subproblemas mas pequenos
2. Alternar entre actualizaciones de variables primales y duales
3. Converge a solucion de alta precision en pocas iteraciones

### Branch-and-Cut (MILP)

Para problemas con variables enteras (MILP):
1. **Branch**: Dividir el espacio de busqueda en subproblemas
2. **Bound**: Acotar usando relajacion LP
3. **Cut**: Agregar planos de corte para estrechar la relajacion

## Comparacion de Solvers

### Tabla Comparativa

| Solver | Algoritmo Principal | Tipo de Problema | Fortalezas |
|--------|---------------------|------------------|------------|
| Gurobi | Simplex / Barrera / Concurrente | LP, QP, MILP | Mejor rendimiento general |
| HiGHS | Simplex Dual | LP, MILP | Rapido para LP densos |
| GLPK | Simplex | LP, MILP | Open source estable, portatil |
| CBC | Branch & Cut | MILP | Robusto para MIP |
| SCIP | Branch & Cut | MILP, MINLP | Framework completo, FOSS |
| ECOS | Punto Interior (IPM) | LP, SOCP | Embebido, liviano, preciso |
| OSQP | ADMM | QP, LP | Escalable, sparse |
| CVXOPT | Punto Interior (IPM) | LP, QP, SOCP, SDP | Programacion convexa general |
| SCS | ADMM + Punto Fijo | LP, SOCP, SDP | Muy escalable, grandes problemas |
| Ipopt | Punto Interior (Barrera) | NLP | Optimizacion no lineal |


### Cuando Usar Cada Solver

| Escenario | Solver Recomendado |
|-----------|-------------------|
| LP densos, open source | HiGHS |
| LP simples, portabilidad | GLPK |
| MIP/MILP robustos | CBC, SCIP |
| Mejor rendimiento general | Gurobi |
| Problemas conicos (SOCP) | ECOS, SCS |
| Optimizacion cuadratica | OSQP, CVXOPT |
| Programacion convexa general | CVXOPT |
| Optimizacion no lineal | Ipopt |
| Problemas muy grandes y sparse | OSQP, SCS |

## Analisis de Sensibilidad

### Costos Reducidos

Para variable xj en el optimo:

```
costo_reducido = coeficiente_objetivo - precio_sombra * coeficiente_restriccion
```

- Si costo_reducido > 0 (max): aumentar xj disminuye objetivo
- Si costo_reducido < 0 (max): aumentar xj incrementa objetivo

### Precios Sombra (Valores Duales)

Para restriccion i:

```
precio_sombra = d(valor_optimo) / d(bi)
```

Interpretacion: El valor marginal de relajar la restriccion i por una unidad.

### Rangos de Factibilidad

- **Rango RHS**: Rango donde el precio sombra permanece valido
- **Rango Objetivo**: Rango donde la base permanece optima

## Analisis de Infactibilidad

### IIS (Conjunto Infactible Irreducible)

Cuando un problema es infactible:

1. **Calcular IIS**: Encontrar subconjunto infactible minimo
2. **Identificar conflictos**: Que restricciones se contradicen
3. **Sugerir correcciones**: Relajar o eliminar restricciones

### Problema Dual

Todo problema primal tiene un dual:

| Primal | Dual |
|--------|------|
| max cTx | min bTy |
| Ax <= b | ATy >= c |
| x >= 0 | y >= 0 |

**Dualidad Fuerte**: Si el primal tiene solucion optima, el dual tambien la tiene con el mismo valor objetivo.

## Benchmark - Fair Comparison

### Warmup

Para comparaciones justas:

```python
config = BenchmarkConfig(
    warmup_runs=1,    # Ejecuciones de calentamiento
    runs_per_problem=3
)
```

El warmup elimina variaciones de JIT/compilacion y cache.

### Metricas de Benchmark

| Metrica | Descripcion |
|---------|------------|
| parse_time | Tiempo de parsing |
| build_time | Construccion Polars |
| solve_time | Resolucion solver |
| total_time | Tiempo total |
| memory_used_mb | MemoriaDelta |
| peak_memory_mb | Pico de memoria |
| iterations | Iteraciones del algoritmo |
| nodes | Nodos explorados (MILP) |

### Configuracion Uniforme

```python
config = BenchmarkConfig(
    fairness_mode=True,
    collect_memory=True,
    collect_detailed_stats=True,
    time_limit=60.0,  # Timeout para evitar solvers lentos
)
```

## Convergencia y Precisión

### Tolerancias Numericas

El sistema usa constantes centralizadas en `src/core/constants.py`:

| Constante | Valor | Proposito |
|-----------|-------|-----------|
| FEASIBILITY_TOLERANCE | 1e-6 | Verificar factibilidad de soluciones |
| OPTIMALITY_TOLERANCE | 1e-6 | Verificar optimalidad |
| BOUND_TOLERANCE | 1e-9 | Verificar limites de variables |
| PARSING_TOLERANCE | 1e-10 | Comparaciones numericas en parsing |
| DEFAULT_INFINITY | 1e30 | Valor predeterminado para infinito |

### Cross-Validation entre Solvers

El sistema puede comparar soluciones de diferentes solvers para detectar discrepancias:

```python
from src.core.verification import compare_solutions

# Comparar 3 solvers en el mismo problema
warnings = compare_solutions(problem, [sol_gurobi, sol_cbc, sol_scip])
if warnings:
    print("Discrepancias encontradas:")
    for w in warnings:
        print(f"  - {w}")
```

## Notas de Rendimiento

### Caracteristicas del Problema

| Caracteristica | Impacto |
|---------------|---------|
| Variables | Mas variables = mas columnas |
| Restricciones | Mas restricciones = mas filas |
| Densidad | Matrices densas son mas lentas |
| Degeneracion | Puede causar ciclacion en Simplex |
| Escalamiento | Mal escalado afecta la precision numerica |

### Parametros de Benchmark

```python
config = BenchmarkConfig(
    warmup_runs=2,
    runs_per_problem=5,
    time_limit=60,
    verbose=False,
    collect_memory=True,
    collect_detailed_stats=True,
)
```

---

## Referencias

1. Dantzig, G. B. (1963). *Linear Programming and Extensions*. Princeton University Press.
2. Bertsimas, D., & Tsitsiklis, J. N. (1997). *Introduction to Linear Optimization*. Athena Scientific.
3. Boyd, S. et al. (2011). *Distributed Optimization and Statistical Learning via ADMM*. Foundations and Trends in ML.
4. Vandenberghe, L. (2010). *The CVXOPT Linear and Quadratic Programming Solver*.
5. O'Donoghue, B. et al. (2016). *Conic Optimization via Operator Splitting and Homogeneous Self-Dual Embedding*. JOTA.
6. Domahidi, A. et al. (2013). *ECOS: An SOCP solver for embedded systems*. ECC.
7. HiGHS Documentation. *Highs Optimization Solver*.
8. GLPK Documentation. *GNU Linear Programming Kit*.
9. COIN-OR Documentation. *CBC*.

Para detalles de API, ver [README.md](../README.md).
