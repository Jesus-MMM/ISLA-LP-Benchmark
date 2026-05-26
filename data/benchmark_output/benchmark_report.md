# Reporte de Benchmarking

Fecha: 2026-05-25 09:49:27

## Resumen
- Total de pruebas: 100
- Exitosas: 100
- Fallidas: 0

## Por Solver

| Solver | Pruebas | Exitosas | Tiempo Promedio |
|--------|---------|----------|-----------------|
| gurobi | 10 | 10 | 133.06ms |
| highs | 10 | 10 | 114.62ms |
| glpk | 10 | 10 | 92.02ms |
| cbc | 10 | 10 | 190.93ms |
| scip | 10 | 10 | 124.93ms |
| ecos | 10 | 10 | 103.69ms |
| osqp | 10 | 10 | 102.92ms |
| cvxopt | 10 | 10 | 125.85ms |
| scs | 10 | 10 | 107.01ms |
| ipopt | 10 | 10 | 553.43ms |

## Detalle de Resultados

| Problema | Solver | Estado | Valor Obj. | Tiempo |
|----------|--------|--------|------------|--------|
| Problema_1 | gurobi | OK | 8.00 | 214.99ms |
| Problema_1 | highs | OK | 8.00 | 163.17ms |
| Problema_1 | glpk | OK | 8.00 | 97.65ms |
| Problema_1 | cbc | OK | 8.00 | 439.81ms |
| Problema_1 | scip | OK | 8.00 | 218.84ms |
| Problema_1 | ecos | OK | 11.43 | 126.53ms |
| Problema_1 | osqp | OK | 11.43 | 86.52ms |
| Problema_1 | cvxopt | OK | 11.43 | 162.61ms |
| Problema_1 | scs | OK | 11.43 | 128.36ms |
| Problema_1 | ipopt | OK | 8.00 | 4071.70ms |
| Problema_2 | gurobi | OK | 406.67 | 110.11ms |
| Problema_2 | highs | OK | 406.67 | 84.90ms |
| Problema_2 | glpk | OK | 406.67 | 84.25ms |
| Problema_2 | cbc | OK | 406.67 | 150.57ms |
| Problema_2 | scip | OK | 406.67 | 121.15ms |
| Problema_2 | ecos | OK | 406.67 | 102.57ms |
| Problema_2 | osqp | OK | 406.67 | 98.30ms |
| Problema_2 | cvxopt | OK | 406.67 | 132.62ms |
| Problema_2 | scs | OK | 406.67 | 118.55ms |
| Problema_2 | ipopt | OK | 406.67 | 160.83ms |
| Problema_3 | gurobi | OK | 68.00 | 157.15ms |
| Problema_3 | highs | OK | 68.00 | 117.12ms |
| Problema_3 | glpk | OK | 68.00 | 137.87ms |
| Problema_3 | cbc | OK | 68.00 | 155.41ms |
| Problema_3 | scip | OK | 68.00 | 144.47ms |
| Problema_3 | ecos | OK | 68.00 | 121.53ms |
| Problema_3 | osqp | OK | 68.00 | 95.94ms |
| Problema_3 | cvxopt | OK | 68.00 | 116.35ms |
| Problema_3 | scs | OK | 68.00 | 94.26ms |
| Problema_3 | ipopt | OK | 68.00 | 116.98ms |
| Problema_4 | gurobi | OK | 1253.33 | 123.34ms |
| Problema_4 | highs | OK | 1253.33 | 106.71ms |
| Problema_4 | glpk | OK | 1253.33 | 86.94ms |
| Problema_4 | cbc | OK | 1253.33 | 188.44ms |
| Problema_4 | scip | OK | 1253.33 | 123.31ms |
| Problema_4 | ecos | OK | 1253.33 | 101.12ms |
| Problema_4 | osqp | OK | 1253.33 | 100.43ms |
| Problema_4 | cvxopt | OK | 1253.33 | 105.30ms |
| Problema_4 | scs | OK | 1253.40 | 123.08ms |
| Problema_4 | ipopt | OK | 1253.33 | 134.97ms |
| Problema_5 | gurobi | OK | 80.00 | 93.34ms |
| Problema_5 | highs | OK | 80.00 | 123.78ms |
| Problema_5 | glpk | OK | 80.00 | 98.22ms |
| Problema_5 | cbc | OK | 80.00 | 160.81ms |
| Problema_5 | scip | OK | 80.00 | 85.84ms |
| Problema_5 | ecos | OK | 80.00 | 77.22ms |
| Problema_5 | osqp | OK | 80.00 | 106.99ms |
| Problema_5 | cvxopt | OK | 80.00 | 104.67ms |
| Problema_5 | scs | OK | 80.00 | 82.64ms |
| Problema_5 | ipopt | OK | 80.00 | 132.90ms |
| Problema_6 | gurobi | OK | 18233.33 | 127.36ms |
| Problema_6 | highs | OK | 18233.33 | 115.27ms |
| Problema_6 | glpk | OK | 18233.33 | 83.82ms |
| Problema_6 | cbc | OK | 18233.33 | 145.80ms |
| Problema_6 | scip | OK | 18233.33 | 92.47ms |
| Problema_6 | ecos | OK | 18233.33 | 99.87ms |
| Problema_6 | osqp | OK | 18233.33 | 110.50ms |
| Problema_6 | cvxopt | OK | 18233.33 | 101.45ms |
| Problema_6 | scs | OK | 18233.33 | 104.63ms |
| Problema_6 | ipopt | OK | 18233.33 | 201.24ms |
| Problema_7 | gurobi | OK | 403.08 | 102.49ms |
| Problema_7 | highs | OK | 403.08 | 88.20ms |
| Problema_7 | glpk | OK | 403.08 | 80.53ms |
| Problema_7 | cbc | OK | 403.08 | 178.29ms |
| Problema_7 | scip | OK | 403.08 | 118.14ms |
| Problema_7 | ecos | OK | 403.08 | 115.35ms |
| Problema_7 | osqp | OK | 403.08 | 112.12ms |
| Problema_7 | cvxopt | OK | 403.08 | 165.44ms |
| Problema_7 | scs | OK | 403.08 | 102.25ms |
| Problema_7 | ipopt | OK | 403.08 | 183.06ms |
| Problema_8 | gurobi | OK | 1020.00 | 151.60ms |
| Problema_8 | highs | OK | 1020.00 | 107.29ms |
| Problema_8 | glpk | OK | 1020.00 | 79.83ms |
| Problema_8 | cbc | OK | 1020.00 | 184.54ms |
| Problema_8 | scip | OK | 1020.00 | 124.84ms |
| Problema_8 | ecos | OK | 1020.00 | 87.02ms |
| Problema_8 | osqp | OK | 1020.00 | 103.21ms |
| Problema_8 | cvxopt | OK | 1020.00 | 108.86ms |
| Problema_8 | scs | OK | 1020.01 | 95.99ms |
| Problema_8 | ipopt | OK | 1020.00 | 205.86ms |
| Problema_9 | gurobi | OK | 71730.77 | 130.53ms |
| Problema_9 | highs | OK | 71730.77 | 123.77ms |
| Problema_9 | glpk | OK | 71730.77 | 100.29ms |
| Problema_9 | cbc | OK | 71730.77 | 137.56ms |
| Problema_9 | scip | OK | 71730.77 | 97.45ms |
| Problema_9 | ecos | OK | 71730.77 | 92.18ms |
| Problema_9 | osqp | OK | 71730.77 | 100.48ms |
| Problema_9 | cvxopt | OK | 71730.77 | 114.96ms |
| Problema_9 | scs | OK | 71731.37 | 118.48ms |
| Problema_9 | ipopt | OK | 71730.77 | 165.83ms |
| Problema_10 | gurobi | OK | 7790.00 | 119.73ms |
| Problema_10 | highs | OK | 7790.00 | 116.03ms |
| Problema_10 | glpk | OK | 7790.00 | 70.83ms |
| Problema_10 | cbc | OK | 7790.00 | 168.07ms |
| Problema_10 | scip | OK | 7790.00 | 122.80ms |
| Problema_10 | ecos | OK | 7790.00 | 113.51ms |
| Problema_10 | osqp | OK | 7790.00 | 114.74ms |
| Problema_10 | cvxopt | OK | 7790.00 | 146.24ms |
| Problema_10 | scs | OK | 5256.92 | 101.85ms |
| Problema_10 | ipopt | OK | 7790.00 | 160.90ms |