"""
Dependency Graph Tools
Builds and analyzes dependency graphs for code architecture visualization
"""

import os
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict

_analysis_cache = {}


def extract_imports(directory: str) -> dict:
    """
    Extracts all import relationships across the codebase

    Args:
        directory: Path to the code directory

    Returns:
        Dict with import map, external dependencies, and internal module links
    """
    imports_map = {}
    external_deps = defaultdict(int)
    internal_modules = set()

    try:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in {
                '.git', '__pycache__', 'node_modules', '.venv', 'venv',
                '.tox', 'dist', 'build', '.pytest_cache', '.mypy_cache',
                'target', '.idea', '.vscode'
            }]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, directory)

                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            source = f.read()

                        tree = ast.parse(source, filepath)
                        file_imports = {
                            "stdlib": [],
                            "external": [],
                            "internal": [],
                            "from_imports": []
                        }

                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    module_name = alias.name
                                    if _is_stdlib(module_name):
                                        file_imports["stdlib"].append(module_name)
                                    elif _is_external(module_name):
                                        file_imports["external"].append(module_name)
                                        external_deps[module_name.split('.')[0]] += 1
                                    else:
                                        file_imports["internal"].append(module_name)
                                        internal_modules.add(module_name)

                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    module_name = node.module
                                    imported_names = [alias.name for alias in node.names]
                                    file_imports["from_imports"].append({
                                        "module": module_name,
                                        "names": imported_names
                                    })
                                    if _is_stdlib(module_name):
                                        file_imports["stdlib"].append(module_name)
                                    elif _is_external(module_name):
                                        file_imports["external"].append(module_name)
                                        external_deps[module_name.split('.')[0]] += 1
                                    else:
                                        file_imports["internal"].append(module_name)
                                        internal_modules.add(module_name)

                        imports_map[rel_path] = file_imports
                    except:
                        pass

        result = {
            "imports": imports_map,
            "external_dependencies": dict(external_deps),
            "internal_modules": sorted(internal_modules),
            "total_files_with_imports": len(imports_map)
        }

        _analysis_cache['imports'] = result
        return result
    except Exception as e:
        return {"error": str(e)}


def build_dependency_matrix(directory: str) -> dict:
    """
    Builds a dependency matrix showing which modules depend on which

    Args:
        directory: Path to the code directory

    Returns:
        Dict with dependency matrix, coupling metrics, and dependency direction
    """
    imports_data = _analysis_cache.get('imports')
    if not imports_data:
        imports_data = extract_imports(directory)

    modules = set()
    for file_path, file_imports in imports_data.get('imports', {}).items():
        module = file_path.replace(os.sep, '.').replace('.py', '')
        modules.add(module)
        for imp in file_imports.get('internal', []):
            modules.add(imp)

    module_list = sorted(modules)
    n = len(module_list)
    index_map = {m: i for i, m in enumerate(module_list)}

    matrix = [[0] * n for _ in range(n)]
    dependents = defaultdict(set)
    dependencies = defaultdict(set)

    for file_path, file_imports in imports_data.get('imports', {}).items():
        source_module = file_path.replace(os.sep, '.').replace('.py', '')
        if source_module not in index_map:
            continue
        src_idx = index_map[source_module]

        for target in file_imports.get('internal', []):
            if target in index_map:
                tgt_idx = index_map[target]
                matrix[src_idx][tgt_idx] += 1
                dependents[target].add(source_module)
                dependencies[source_module].add(target)

    couplings = []
    for file_path, file_imports in imports_data.get('imports', {}).items():
        source_module = file_path.replace(os.sep, '.').replace('.py', '')
        for target in file_imports.get('internal', []):
            if target in index_map:
                couplings.append({
                    "from": source_module,
                    "to": target,
                    "file": file_path
                })

    result = {
        "matrix": matrix,
        "modules": module_list,
        "couplings": couplings,
        "total_couplings": len(couplings),
        "dependents": {k: list(v) for k, v in dependents.items()},
        "dependencies": {k: list(v) for k, v in dependencies.items()}
    }

    _analysis_cache['coupling'] = result
    return result


def detect_cyclic_dependencies(directory: str) -> dict:
    """
    Detects cyclic dependencies between modules using DFS on the dependency graph

    Args:
        directory: Path to the code directory

    Returns:
        Dict with detected cycles, cycle members, and severity
    """
    dep_matrix = _analysis_cache.get('coupling')
    if not dep_matrix:
        dep_matrix = build_dependency_matrix(directory)

    graph = defaultdict(set)
    for coupling in dep_matrix.get('couplings', []):
        graph[coupling['from']].add(coupling['to'])

    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                if cycle not in cycles:
                    cycles.append(cycle)
                return True

        path.pop()
        rec_stack.discard(node)
        return False

    all_nodes = list(graph.keys())
    for node in all_nodes:
        if node not in visited:
            dfs(node)

    cycle_severity = []
    for cycle in cycles:
        severity = (
            "high" if len(cycle) <= 3 else
            "medium" if len(cycle) <= 6 else "low"
        )
        cycle_severity.append({
            "cycle": cycle,
            "length": len(cycle),
            "severity": severity,
            "members": list(set(cycle))
        })

    result = {
        "cycles": cycle_severity,
        "total_cycles": len(cycle_severity),
        "has_cycles": len(cycle_severity) > 0,
        "high_severity_cycles": sum(1 for c in cycle_severity if c["severity"] == "high"),
        "suggestion": "Break cycles by extracting shared dependencies into a common module"
            if cycle_severity else "No cyclic dependencies detected"
    }

    _analysis_cache['cycles'] = result
    return result


def calculate_coupling_metrics(directory: str) -> dict:
    """
    Calculates coupling and cohesion metrics for each module

    Args:
        directory: Path to the code directory

    Returns:
        Dict with afferent/efferent coupling, instability, and abstractness metrics
    """
    dep_matrix = _analysis_cache.get('coupling')
    if not dep_matrix:
        dep_matrix = build_dependency_matrix(directory)

    dependents = dep_matrix.get('dependents', {})
    dependencies = dep_matrix.get('dependencies', {})
    all_modules = set(list(dependents.keys()) + list(dependencies.keys()))

    metrics = {}
    for module in all_modules:
        ca = len(dependents.get(module, set()))  # Afferent (incoming)
        ce = len(dependencies.get(module, set()))  # Efferent (outgoing)

        instability = ce / (ca + ce) if (ca + ce) > 0 else 0

        metrics[module] = {
            "afferent_coupling": ca,
            "efferent_coupling": ce,
            "instability": round(instability, 3),
            "total_dependencies": ca + ce,
            "classification": (
                "unstable_dependent" if instability < 0.3 and ca > 0 else
                "independent" if instability > 0.7 else
                "bidirectional" if 0.3 <= instability <= 0.7 else
                "abstract_stable" if instability == 0 and ca > 0 else
                "isolated"
            )
        }

    result = {
        "module_metrics": metrics,
        "average_instability": round(
            sum(m["instability"] for m in metrics.values()) / len(metrics), 3
        ) if metrics else 0,
        "highly_stable_modules": [
            k for k, v in metrics.items() if v["instability"] < 0.3
        ],
        "highly_unstable_modules": [
            k for k, v in metrics.items() if v["instability"] > 0.7
        ],
        "main_seq_distance": _calculate_main_seq_distance(metrics)
    }

    _analysis_cache['coupling_metrics'] = result
    return result


def _calculate_main_seq_distance(metrics: dict) -> dict:
    """Calculate distance from the main sequence (ideal line)"""
    distances = {}
    for module, m in metrics.items():
        d = abs(m["instability"] - 0.5)
        distances[module] = round(d, 3)
    return distances


def build_dependency_graph_json(directory: str) -> dict:
    """
    Builds a complete dependency graph in JSON format for visualization

    Args:
        directory: Path to the code directory

    Returns:
        Dict with nodes and edges formatted for D3.js/vis.js visualization
    """
    dep_matrix = _analysis_cache.get('coupling')
    if not dep_matrix:
        dep_matrix = build_dependency_matrix(directory)

    coupling_metrics = _analysis_cache.get('coupling_metrics')
    if not coupling_metrics:
        coupling_metrics = calculate_coupling_metrics(directory)

    nodes = []
    node_ids = {}
    module_metrics = coupling_metrics.get('module_metrics', {})

    for i, module in enumerate(dep_matrix.get('modules', [])):
        metrics = module_metrics.get(module, {})
        instability = metrics.get('instability', 0.5)

        node_ids[module] = i
        nodes.append({
            "id": i,
            "name": module,
            "instability": instability,
            "group": metrics.get('classification', 'unknown'),
            "size": max(5, 20 * (1 - instability))
        })

    edges = []
    for coupling in dep_matrix.get('couplings', []):
        source = coupling.get('from')
        target = coupling.get('to')
        if source in node_ids and target in node_ids:
            edges.append({
                "source": node_ids[source],
                "target": node_ids[target],
                "weight": 1,
                "curved": False
            })

    result = {
        "graph": {
            "nodes": nodes,
            "edges": edges
        },
        "node_count": len(nodes),
        "edge_count": len(edges),
        "density": round(
            (2 * len(edges)) / (len(nodes) * (len(nodes) - 1)), 4
        ) if len(nodes) > 1 else 0
    }

    _analysis_cache['graph_json'] = result
    return result


STDLIB_MODULES = {
    'os', 'sys', 're', 'json', 'math', 'time', 'datetime', 'collections',
    'itertools', 'functools', 'pathlib', 'typing', 'hashlib', 'uuid',
    'copy', 'enum', 'io', 'abc', 'argparse', 'logging', 'threading',
    'multiprocessing', 'subprocess', 'socket', 'http', 'urllib', 'xml',
    'csv', 'string', 'random', 'statistics', 'decimal', 'fractions',
    'pickle', 'shelve', 'sqlite3', 'zoneinfo', 'dataclasses', 'inspect',
    'ast', 'textwrap', 'base64', 'binascii', 'struct', 'traceback',
    'warnings', 'contextlib', 'importlib', 'pkgutil', 'weakref',
    'numbers', 'operator', 'bisect', 'array', 'queue', 'configparser',
    'tempfile', 'fileinput', 'fnmatch', 'linecache', 'tokenize',
    'calendar', 'pprint', 'profile', 'pstats', 'unittest', 'doctest'
}


def _is_stdlib(module_name: str) -> bool:
    base = module_name.split('.')[0]
    return base in STDLIB_MODULES


EXTERNAL_PREFIXES = {
    'django', 'flask', 'fastapi', 'sqlalchemy', 'pydantic', 'crewai',
    'crewai_tools', 'numpy', 'pandas', 'scipy', 'sklearn', 'torch',
    'tensorflow', 'matplotlib', 'seaborn', 'plotly', 'bokeh', 'streamlit',
    'gradio', 'pytest', 'mock', 'requests', 'httpx', 'aiohttp',
    'asyncio', 'click', 'typer', 'rich', 'tqdm', 'PIL', 'opencv',
    'beautifulsoup4', 'lxml', 'boto3', 'azure', 'gcloud', 'redis',
    'celery', 'kombu', 'docker', 'kubernetes', 'grpc', 'protobuf',
    'graphql', 'strawberry', 'graphene', 'websockets', 'sse_starlette',
    'uvicorn', 'gunicorn', 'pydantic_settings', 'python_dotenv',
    'networkx', 'community', 'igraph', 'visjs', 'pyvis', 'dash',
    'plotly', 'altair', 'vega_datasets'
}


def _is_external(module_name: str) -> bool:
    base = module_name.split('.')[0]
    return base in EXTERNAL_PREFIXES or not base.isidentifier()
