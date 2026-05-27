"""
Pytest configuration for test isolation.
Clean up any mock modules that may interfere with real module imports.
This runs at session start and after specific test modules.
"""
import sys


# Clean mock modules if they exist (from test_cli/test_benchmark.py)
# These mocks interfere with actual tests for visualization and analysis modules
modules_to_clean = [
    'src.visualization',
    'src.visualization.benchmark_plots', 
    'src.visualization.visualization',
    'src.analysis.benchmark_results',
    'src.analysis.benchmark_report',
]


def pytest_configure(config):
    """Run before test collection to clean mock modules."""
    for mod in modules_to_clean:
        if mod in sys.modules:
            del sys.modules[mod]


def pytest_collection_modifyitems(items):
    """Clean up modules after test_cli/test_benchmark.py tests are collected."""
    # Find test items from test_cli/test_benchmark.py
    [item for item in items if 'test_cli/test_benchmark.py' in item.nodeid]
    # We'll clean up after them in the test file itself, but also ensure cleanup here
    for mod in modules_to_clean:
        if mod in sys.modules:
            del sys.modules[mod]