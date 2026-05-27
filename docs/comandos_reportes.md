# Comandos para Generar Reportes (v1.6.0)

## 1. Reporte Individual (Single Report)

### Con Gurobi
```bash
python -m src.cli data/problem.txt --pdf --solver gurobi
```
**Salida:** `data/problem.pdf`

### Con CBC
```bash
python -m src.cli data/problem.txt --pdf --solver cbc
```
**Salida:** `data/problem.pdf`

### Con SCIP
```bash
python -m src.cli data/problem.txt --pdf --solver scip
```
**Salida:** `data/problem.pdf`

### Con HiGHS
```bash
python -m src.cli data/problem.txt --pdf --solver highs
```
**Salida:** `data/problem.pdf`

### Automático (detecta solver disponible)
```bash
python -m src.cli data/problem.txt --pdf
```
**Salida:** `data/problem.pdf`

---

## 2. Reporte Multi-Problema (Multi-Problem Report)

### Con múltiples solvers
```bash
python -m src.cli data/problem.txt --multi --solvers gurobi cbc --pdf
```
**Salida:** `data/problem_multi.pdf`

### Con todos los solvers disponibles
```bash
python -m src.cli data/problem.txt --multi --solvers gurobi cbc scip highs --pdf
```
**Salida:** `data/problem_multi.pdf`

---

## 3. Reporte de Benchmark (Comparativo)

### Benchmark básico con PDF
```bash
python -m src.cli --benchmark --pdf data/problem.txt
```
**Salida:** `data/benchmark_output/benchmark_report.pdf`

### Benchmark con múltiples problemas
```bash
python -m src.cli --benchmark --pdf data/problem.txt data/milp_example.txt
```
**Salida:** `data/benchmark_output/benchmark_report.pdf`

### Benchmark con solvers específicos
```bash
python -m src.cli --benchmark --solvers gurobi cbc scip --pdf data/problem.txt
```
**Salida:** `data/benchmark_output/benchmark_report.pdf`

### Benchmark con límite de tiempo
```bash
python -m src.cli --benchmark --all-solvers --timeout 30 --repetitions 3 data/problem.txt
```

### Benchmark con exportación CSV
```bash
python -m src.cli --benchmark --solvers gurobi highs --output-csv results.csv data/problem.txt
```

---

## 4. Ejemplos de Uso con Diferentes Problemas

### Problema MILP (Programación Lineal Entera)
```bash
python -m src.cli data/milp_example.txt --pdf --solver gurobi
```

### Benchmark de múltiples problemas
```bash
python -m src.cli --benchmark --pdf data/problem.txt data/milp_example.txt
```

---

## 5. Estructura de Reportes Generados

### Secciones en Reporte Individual (`LPAnalysis`):
1. Portada
2. Resumen Ejecutivo
3. Datos del Problema
4. Función Objetivo
5. Restricciones
6. Solución Óptima
7. Análisis de Holgura y Precios Sombra
8. Costos Reducidos
9. Validación del Modelo
10. Configuración del Solver
11. Base Óptima
12. Métricas Numéricas
13. Análisis de Sensibilidad
14. Gráfico (si es 2D)
15. Log de Progreso
16. Interpretación Ejecutiva
17. Referencias Teóricas

### Secciones en Reporte Multi-Problema (`MultiLPAnalysis`):
1. Portada con estadísticas generales
2. Resumen ejecutivo con tabla de resultados
3. Página individual por problema (función objetivo, restricciones, solución, holguras, gráfico)
4. Resumen de tiempos por problema

### Secciones en Reporte Benchmark (`BenchmarkReport`):
1. Portada
2. Resumen Estadístico
3. Comparación por Solver
4. Resultados Detallados
5. Definiciones de Problemas
6. Gráfico de Tiempo Promedio
7. Gráfico de Tasa de Éxito
8. Gráfico de Memoria
9. Perfiles de Rendimiento
10. Análisis de Escalabilidad
11. Matriz de Correlación
12. Detección de Outliers
13. Recomendaciones
14. Versiones de Software
15. Análisis de Memoria Avanzado

---

## 6. Formatos de Exportación Soportados

| Formato | Extensión | Descripción |
|---------|-----------|-------------|
| PDF | `.pdf` | Reporte visual con gráficos |
| CSV | `.csv` | Datos tabulares para análisis |
| JSON | `.json` | Estructurado para APIs |
| Markdown | `.md` | Documentación ligera |
| HTML | `.html` | Web con gráficos embebidos (benchmark) |
| PNG | `.png` | Gráfico de región factible (2D) |

---

## Notas Importantes

- Todos los reportes usan márgenes de 15mm (multi-problema) o 20mm (individual/benchmark)
- Los gráficos se centran respetando los márgenes
- Formatos soportados: `.txt` (formato estándar LP), `.lp` (CPLEX/LP)
- Solvers soportados: `gurobi`, `cbc`, `scip`, `highs`, `glpk`, `ecos`, `osqp`, `cvxopt`, `scs`, `ipopt`
- Ejecutar `python -m src.cli --list-solvers` para ver solvers disponibles en el sistema
- Usar `--log-level DEBUG` para ver información detallada de diagnóstico
- Tras `pip install -e .`, usar `isla` como atajo: `isla data/problem.txt --pdf`
