"""
Aplicacion web FastAPI + HTMX para resolver problemas de PL.
"""

import time
import uuid
from typing import Optional

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse

from ..parser import LPParser, MPSParser
from ..solver import SolverConfig, SolverRegistry
from ..core import LinearProblem


_problems: dict[str, LinearProblem] = {}
_solutions: dict[str, dict] = {}


def _problem_to_html(problem: LinearProblem, pid: str) -> str:
    """Convierte un problema a HTML."""
    obj_expr = " + ".join(f"{c} {v}" for v, c in problem.objective.items())
    rows_html = "".join(
        f"<tr><td>{c.name or f'C{i}'}</td><td>{' + '.join(f'{coeff} {var}' for var, coeff in c.coefficients.items())}</td>"
        f"<td>{c.sense}</td><td>{c.rhs}</td></tr>"
        for i, c in enumerate(problem.constraints)
    )
    bounds_html = "".join(
        f"<tr><td>{var}</td><td>{problem.variable_types.get(var, 'continuous')}</td>"
        f"<td>{problem.bounds[var].lower if var in problem.bounds and problem.bounds[var].lower is not None else '-inf'}</td>"
        f"<td>{problem.bounds[var].upper if var in problem.bounds and problem.bounds[var].upper is not None else '+inf'}</td></tr>"
        for var in problem.variables
    )
    return f"""
    <div class="card">
        <div class="card-header"><h3>Problema: {problem.name or 'Sin nombre'}</h3></div>
        <div class="card-body">
            <p><strong>Sentido:</strong> {problem.sense}</p>
            <p><strong>Objetivo:</strong> {obj_expr}</p>
            <p><strong>Variables:</strong> {len(problem.variables)} | <strong>Restricciones:</strong> {len(problem.constraints)}</p>

            <h4>Restricciones</h4>
            <table class="table">
                <thead><tr><th>Nombre</th><th>Expresion</th><th>Sentido</th><th>RHS</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>

            <h4>Variables</h4>
            <table class="table">
                <thead><tr><th>Variable</th><th>Tipo</th><th>Inferior</th><th>Superior</th></tr></thead>
                <tbody>{bounds_html}</tbody>
            </table>

            <form hx-post="/solve/{pid}" hx-target="#solution" hx-swap="innerHTML">
                <div class="mb-3">
                    <label class="form-label">Seleccionar solver:</label>
                    <select name="solver" class="form-select">
                        {"".join(f'<option value="{s}">{s}</option>' for s in SolverRegistry.list_solvers(available_only=True))}
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Time limit (s):</label>
                    <input type="number" name="time_limit" value="300" class="form-control" style="width:100px">
                </div>
                <button type="submit" class="btn btn-primary">Resolver</button>
            </form>
        </div>
    </div>
    <div id="solution"></div>
    """


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ISLA LP Solver Web</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <style>
        body {{ padding-top: 20px; }}
        .card {{ margin-bottom: 20px; }}
        .table {{ font-size: 0.9em; }}
        .hero {{ text-align: center; padding: 40px 0; }}
        .hero h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .hero p {{ color: #888; font-size: 1.1em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>ISLA LP Solver</h1>
            <p>Interfaz web para resolver problemas de programacion lineal</p>
        </div>
        {content}
    </div>
</body>
</html>"""


def create_app() -> FastAPI:
    """Crea y configura la aplicacion FastAPI."""
    app = FastAPI(title="ISLA LP Solver Web", version="1.8.1")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        content = """
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header"><h3>Cargar Problema</h3></div>
                    <div class="card-body">
                        <form hx-encoding="multipart/form-data" hx-post="/upload" hx-target="#result" hx-swap="innerHTML">
                            <div class="mb-3">
                                <label class="form-label">Archivo LP o MPS:</label>
                                <input type="file" name="file" class="form-control" accept=".lp,.mps,.txt">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">O pega el texto del problema:</label>
                                <textarea name="text" class="form-control" rows="5" placeholder="max: x + y; x + y <= 10; x >= 0; y >= 0"></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary">Parsear</button>
                        </form>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header"><h3>Problemas de Ejemplo</h3></div>
                    <div class="card-body">
                        <button class="btn btn-outline-secondary mb-2" hx-post="/load-example" hx-vals='{"example": "simple"}' hx-target="#result" hx-swap="innerHTML">Simple (max)</button>
                        <button class="btn btn-outline-secondary mb-2" hx-post="/load-example" hx-vals='{"example": "mip"}' hx-target="#result" hx-swap="innerHTML">MILP</button>
                        <button class="btn btn-outline-secondary mb-2" hx-post="/load-example" hx-vals='{"example": "netlib"}' hx-target="#result" hx-swap="innerHTML">Netlib-like</button>
                    </div>
                </div>
            </div>
        </div>
        <div id="result"></div>
        <div id="solution"></div>
        """
        return HTML_TEMPLATE.format(content=content)

    @app.post("/upload")
    async def upload(file: Optional[UploadFile] = None, text: str = Form("")):
        if file and file.filename:
            content = (await file.read()).decode("utf-8")
        elif text.strip():
            content = text
        else:
            return HTMLResponse("<div class='alert alert-danger'>No se proporciono ningun problema.</div>")

        try:
            if content.strip().upper().startswith("NAME") or content.strip().upper().startswith("ROWS"):
                problem = MPSParser(content).parse()
            else:
                problem = LPParser(content).parse()

            pid = str(uuid.uuid4())
            _problems[pid] = problem
            return HTMLResponse(_problem_to_html(problem, pid))
        except Exception as e:
            return HTMLResponse(f"<div class='alert alert-danger'>Error al parsear: {e}</div>")

    @app.post("/load-example")
    async def load_example(example: str = Form("simple")):
        from src.utils.problem_generator import ProblemGenerator
        gen = ProblemGenerator(random_state=42)
        if example == "mip":
            problem = gen.generate_milp(n_vars=4, n_constraints=6, n_int_vars=2)
        elif example == "netlib":
            problem = gen.generate_netlib_like("afiro")
        else:
            problem = gen.generate_lp(n_vars=3, n_constraints=4)
        pid = str(uuid.uuid4())
        _problems[pid] = problem
        return HTMLResponse(_problem_to_html(problem, pid))

    @app.post("/solve/{pid}")
    async def solve(pid: str, solver: str = Form(...), time_limit: float = Form(300.0)):
        if pid not in _problems:
            return HTMLResponse("<div class='alert alert-danger'>Problema no encontrado.</div>")

        problem = _problems[pid]
        solver_class = SolverRegistry.get(solver)
        if solver_class is None:
            return HTMLResponse(f"<div class='alert alert-danger'>Solver '{solver}' no disponible.</div>")

        try:
            config = SolverConfig(time_limit=time_limit if time_limit > 0 else None)
            inst = solver_class(problem, config)
            start = time.perf_counter()
            solution = inst.solve()
            elapsed = time.perf_counter() - start

            sol_id = str(uuid.uuid4())
            _solutions[sol_id] = {
                "solver": solver,
                "status": solution.status,
                "objective_value": solution.objective_value,
                "variables": solution.variables,
                "time_ms": round(elapsed * 1000, 2),
                "numerical_quality": solution.numerical_quality,
            }

            var_rows = "".join(
                f"<tr><td>{v}</td><td>{val:.6f}</td></tr>"
                for v, val in solution.variables.items()
            )
            nq = solution.numerical_quality
            nq_html = ""
            if nq:
                nq_html = f"""
                <div class="card mt-3">
                    <div class="card-header"><h4>Calidad Numerica</h4></div>
                    <div class="card-body">
                        <table class="table">
                            <tr><td>Max bound viol</td><td>{nq.max_bound_viol or 'N/A'}</td></tr>
                            <tr><td>Max dual viol</td><td>{nq.max_dual_viol or 'N/A'}</td></tr>
                            <tr><td>Max slack viol</td><td>{nq.max_slack_viol or 'N/A'}</td></tr>
                            <tr><td>MIP Gap</td><td>{nq.mip_gap or 'N/A'}</td></tr>
                        </table>
                    </div>
                </div>
                """

            return HTMLResponse(f"""
            <div class="card mt-3">
                <div class="card-header">
                    <h3>Resultado ({solver})</h3>
                </div>
                <div class="card-body">
                    <p><strong>Estado:</strong> {solution.status}</p>
                    <p><strong>Valor optimo:</strong> {solution.objective_value}</p>
                    <p><strong>Tiempo:</strong> {_solutions[sol_id]['time_ms']} ms</p>

                    <h4>Variables</h4>
                    <table class="table">
                        <thead><tr><th>Variable</th><th>Valor</th></tr></thead>
                        <tbody>{var_rows}</tbody>
                    </table>

                    {nq_html}
                </div>
            </div>
            """)
        except Exception as e:
            return HTMLResponse(f"<div class='alert alert-danger'>Error al resolver: {e}</div>")

    return app


app = create_app()
