# Reporte de Benchmarking

Fecha: 2026-06-01 14:41:38

## Resumen
- Total de pruebas: 100
- Exitosas: 100
- Fallidas: 0

## Por Solver

| Solver | Pruebas | Exitosas | Tiempo Promedio |
|--------|---------|----------|-----------------|
| gurobi | 10 | 10 | 132.16ms |
| highs | 10 | 10 | 80.72ms |
| glpk | 10 | 10 | 79.49ms |
| cbc | 10 | 10 | 123.85ms |
| scip | 10 | 10 | 89.49ms |
| ecos | 10 | 10 | 83.72ms |
| osqp | 10 | 10 | 98.26ms |
| cvxopt | 10 | 10 | 95.18ms |
| scs | 10 | 10 | 84.36ms |
| ipopt | 10 | 10 | 123.72ms |

## Detalle de Resultados

| Problema | Solver | Estado | Valor Obj. | Tiempo |
|----------|--------|--------|------------|--------|
| Problema_1 | gurobi | OK | 8.00 | 455.30ms |
| Problema_1 | highs | OK | 8.00 | 77.38ms |
| Problema_1 | glpk | OK | 8.00 | 80.91ms |
| Problema_1 | cbc | OK | 8.00 | 127.27ms |
| Problema_1 | scip | OK | 8.00 | 95.26ms |
| Problema_1 | ecos | OK | 11.43 | 108.14ms |
| Problema_1 | osqp | OK | 11.43 | 106.63ms |
| Problema_1 | cvxopt | OK | 11.43 | 87.61ms |
| Problema_1 | scs | OK | 11.43 | 76.47ms |
| Problema_1 | ipopt | OK | 8.00 | 95.73ms |
| Problema_2 | gurobi | OK | 406.67 | 83.22ms |
| Problema_2 | highs | OK | 406.67 | 76.95ms |
| Problema_2 | glpk | OK | 406.67 | 73.78ms |
| Problema_2 | cbc | OK | 406.67 | 120.27ms |
| Problema_2 | scip | OK | 406.67 | 94.06ms |
| Problema_2 | ecos | OK | 406.67 | 92.28ms |
| Problema_2 | osqp | OK | 406.67 | 106.54ms |
| Problema_2 | cvxopt | OK | 406.67 | 95.77ms |
| Problema_2 | scs | OK | 406.67 | 78.18ms |
| Problema_2 | ipopt | OK | 406.67 | 100.18ms |
| Problema_3 | gurobi | OK | 68.00 | 84.62ms |
| Problema_3 | highs | OK | 68.00 | 78.69ms |
| Problema_3 | glpk | OK | 68.00 | 75.62ms |
| Problema_3 | cbc | OK | 68.00 | 116.48ms |
| Problema_3 | scip | OK | 68.00 | 87.94ms |
| Problema_3 | ecos | OK | 68.00 | 73.21ms |
| Problema_3 | osqp | OK | 68.00 | 103.33ms |
| Problema_3 | cvxopt | OK | 68.00 | 108.51ms |
| Problema_3 | scs | OK | 68.00 | 85.61ms |
| Problema_3 | ipopt | OK | 68.00 | 104.51ms |
| Problema_4 | gurobi | OK | 1253.33 | 83.92ms |
| Problema_4 | highs | OK | 1253.33 | 82.59ms |
| Problema_4 | glpk | OK | 1253.33 | 80.68ms |
| Problema_4 | cbc | OK | 1253.33 | 142.66ms |
| Problema_4 | scip | OK | 1253.33 | 82.40ms |
| Problema_4 | ecos | OK | 1253.33 | 83.02ms |
| Problema_4 | osqp | OK | 1253.33 | 162.29ms |
| Problema_4 | cvxopt | OK | 1253.33 | 105.02ms |
| Problema_4 | scs | OK | 1253.40 | 90.22ms |
| Problema_4 | ipopt | OK | 1253.33 | 112.64ms |
| Problema_5 | gurobi | OK | 80.00 | 91.38ms |
| Problema_5 | highs | OK | 80.00 | 77.52ms |
| Problema_5 | glpk | OK | 80.00 | 78.09ms |
| Problema_5 | cbc | OK | 80.00 | 119.77ms |
| Problema_5 | scip | OK | 80.00 | 89.51ms |
| Problema_5 | ecos | OK | 80.00 | 78.16ms |
| Problema_5 | osqp | OK | 80.00 | 82.03ms |
| Problema_5 | cvxopt | OK | 80.00 | 108.50ms |
| Problema_5 | scs | OK | 80.00 | 95.12ms |
| Problema_5 | ipopt | OK | 80.00 | 116.79ms |
| Problema_6 | gurobi | OK | 18233.33 | 88.40ms |
| Problema_6 | highs | OK | 18233.33 | 78.95ms |
| Problema_6 | glpk | OK | 18233.33 | 75.84ms |
| Problema_6 | cbc | OK | 18233.33 | 126.26ms |
| Problema_6 | scip | OK | 18233.33 | 88.34ms |
| Problema_6 | ecos | OK | 18233.33 | 78.97ms |
| Problema_6 | osqp | OK | 18233.33 | 81.69ms |
| Problema_6 | cvxopt | OK | 18233.33 | 91.82ms |
| Problema_6 | scs | OK | 18233.33 | 87.59ms |
| Problema_6 | ipopt | OK | 18233.33 | 143.01ms |
| Problema_7 | gurobi | OK | 403.08 | 89.65ms |
| Problema_7 | highs | OK | 403.08 | 75.44ms |
| Problema_7 | glpk | OK | 403.08 | 82.09ms |
| Problema_7 | cbc | OK | 403.08 | 120.03ms |
| Problema_7 | scip | OK | 403.08 | 93.36ms |
| Problema_7 | ecos | OK | 403.08 | 80.96ms |
| Problema_7 | osqp | OK | 403.08 | 81.42ms |
| Problema_7 | cvxopt | OK | 403.08 | 84.83ms |
| Problema_7 | scs | OK | 403.08 | 96.32ms |
| Problema_7 | ipopt | OK | 403.08 | 132.73ms |
| Problema_8 | gurobi | OK | 1020.00 | 106.48ms |
| Problema_8 | highs | OK | 1020.00 | 89.32ms |
| Problema_8 | glpk | OK | 1020.00 | 86.94ms |
| Problema_8 | cbc | OK | 1020.00 | 123.31ms |
| Problema_8 | scip | OK | 1020.00 | 84.28ms |
| Problema_8 | ecos | OK | 1020.00 | 78.13ms |
| Problema_8 | osqp | OK | 1020.00 | 82.32ms |
| Problema_8 | cvxopt | OK | 1020.00 | 86.07ms |
| Problema_8 | scs | OK | 1020.01 | 74.45ms |
| Problema_8 | ipopt | OK | 1020.00 | 143.80ms |
| Problema_9 | gurobi | OK | 71730.77 | 111.16ms |
| Problema_9 | highs | OK | 71730.77 | 82.52ms |
| Problema_9 | glpk | OK | 71730.77 | 78.42ms |
| Problema_9 | cbc | OK | 71730.77 | 119.06ms |
| Problema_9 | scip | OK | 71730.77 | 85.77ms |
| Problema_9 | ecos | OK | 71730.77 | 80.30ms |
| Problema_9 | osqp | OK | 71730.77 | 84.96ms |
| Problema_9 | cvxopt | OK | 71730.77 | 90.47ms |
| Problema_9 | scs | OK | 71731.37 | 83.56ms |
| Problema_9 | ipopt | OK | 71730.77 | 134.19ms |
| Problema_10 | gurobi | OK | 7790.00 | 127.44ms |
| Problema_10 | highs | OK | 7790.00 | 87.88ms |
| Problema_10 | glpk | OK | 7790.00 | 82.50ms |
| Problema_10 | cbc | OK | 7790.00 | 123.43ms |
| Problema_10 | scip | OK | 7790.00 | 94.02ms |
| Problema_10 | ecos | OK | 7790.00 | 83.99ms |
| Problema_10 | osqp | OK | 7790.00 | 91.37ms |
| Problema_10 | cvxopt | OK | 7790.00 | 93.19ms |
| Problema_10 | scs | OK | 5256.92 | 76.12ms |
| Problema_10 | ipopt | OK | 7790.00 | 153.58ms |