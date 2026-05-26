"""
Handler para el modo benchmark.
"""

from pathlib import Path
from typing import Optional


from src.parser import MultiLPParser
from src.solver import (
    BenchmarkRunner, BenchmarkConfig
)
from src.analysis import export_benchmark_results
from src.cli import get_system_info
from src.visualization.benchmark_plots import BenchmarkPlotter as BenchmarkVisualizer


def run_benchmark(
    input_path: Optional[Path] = None,
    solvers: Optional[list[str]] = None,
    repetitions: int = 1,
    visualize: bool = False,
    output_csv: Optional[str] = None,
    plot_comparison: bool = False,
    output_dir: Optional[str] = None,
    verbose: bool = False,
    pdf: bool = False,
    quiet: bool = False,
    time_limit: Optional[float] = None,
) -> int:
    """Ejecuta el modo benchmark."""
    solvers = solvers or ['gurobi']
    output_dir_val = Path(output_dir) if output_dir else Path('data/benchmark_output')
    
    problems = []
    
    system_info = get_system_info()
    
    if input_path and input_path.exists():
        with open(input_path, 'r') as f:
            content = f.read()
        
        if '---' in content:
            parser = MultiLPParser(content)
            parsed_problems = parser.parse_all()
            for i, p in enumerate(parsed_problems, 1):
                problems.append((f"Problema_{i}", _problem_to_text(p)))
        else:
            problems.append((input_path.stem, content))
    else:
        problems = [
            ("Problema_1", "max Z = x + y\nx + y <= 10\nx >= 0\ny >= 0"),
            ("Problema_2", "max Z = 3x + 5y\n2x + y <= 18\nx + 3y <= 24\nx >= 0\ny >= 0"),
            ("Problema_3", "min Z = 2x + 3y\nx + y >= 5\n2x + y >= 8\nx >= 0\ny >= 0"),
        ]
    
    if not quiet:
        print(f"\n{'='*50}")
        print("BENCHMARK")
        print("="*50)
        print(f"Problems: {len(problems)}")
        print(f"Solvers: {', '.join(solvers)}")
        print(f"Repetitions: {repetitions}")
        print(f"Output: {output_dir}")
        if time_limit:
            print(f"Time limit: {time_limit}s")
        print("="*50 + "\n")
    
    config = BenchmarkConfig(
        verbose=verbose,
        runs_per_problem=repetitions,
        time_limit=time_limit,
    )
    runner = BenchmarkRunner(config)
    runner.run(problems, solvers)
    
    runner.print_summary()
    
    if output_csv:
        runner.export_csv(Path(output_csv))
        print(f"\nCSV exported to: {output_csv}")
    
    if plot_comparison or visualize:
        print("\nGenerating plots...")
        viz = BenchmarkVisualizer(runner)
        viz.generate_all_plots(output_dir_val)
        print(f"Plots saved to: {output_dir_val}")
    
    if pdf:
        print("\nGenerating PDF report...")
        from src.analysis import BenchmarkReport
        
        # Create output directory if it doesn't exist
        output_dir_path = Path(output_dir) if output_dir else Path('data/benchmark_output')
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        pdf_path = output_dir_path / "benchmark_report.pdf"
        benchmark_report = BenchmarkReport(runner, system_info)
        benchmark_report.generate(str(pdf_path))
        print(f"PDF saved to: {pdf_path}")
    
    export_benchmark_results(runner, output_dir_val, formats=['json', 'csv', 'md'])
    print(f"\nFull results saved to: {output_dir}")
    
    return 0


def _problem_to_text(problem) -> str:
    """Convierte un LinearProblem a texto."""
    sense = problem.sense.upper()
    terms = []
    for var, coeff in problem.objective.items():
        if coeff >= 0:
            terms.append(f"+{coeff}{var}")
        else:
            terms.append(f"{coeff}{var}")
    obj = " ".join(terms) if terms else "0"
    if obj.startswith("+"):
        obj = obj[1:]
    lines = [f"{sense} Z = {obj}"]
    
    for c in problem.constraints:
        c_terms = []
        for var, coeff in c.coefficients.items():
            if coeff >= 0:
                c_terms.append(f"+{coeff}{var}")
            else:
                c_terms.append(f"{coeff}{var}")
        c_str = " ".join(c_terms)
        if c_str.startswith("+"):
            c_str = c_str[1:]
        lines.append(f"{c_str} {c.sense} {c.rhs}")
    
    for var, bound in problem.bounds.items():
        if bound.lower is not None and bound.upper is not None:
            lines.append(f"{bound.lower} <= {var} <= {bound.upper}")
        elif bound.lower is not None:
            lines.append(f"{var} >= {bound.lower}")
        elif bound.upper is not None:
            lines.append(f"{var} <= {bound.upper}")
    
    return "\n".join(lines)
