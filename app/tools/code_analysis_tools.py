"""
Code Analysis Tools
Provides file structure analysis, module organization, and technical debt detection
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict


# Shared analysis cache for inter-agent communication
_analysis_cache = {}


def analyze_file_structure(directory: str) -> dict:
    """
    Analyzes the file structure of a codebase with language detection and size metrics

    Args:
        directory: Path to the code directory

    Returns:
        Dict with file inventory, module organization, and language distribution
    """
    structure = {
        "files": [],
        "modules": defaultdict(list),
        "total_lines": 0,
        "total_files": 0,
        "languages": defaultdict(lambda: {"count": 0, "lines": 0}),
        "max_file_size": 0,
        "largest_files": []
    }

    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.go': 'go',
        '.rs': 'rust',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin'
    }

    try:
        for root, dirs, files in os.walk(directory):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in {
                '.git', '__pycache__', 'node_modules', '.venv', 'venv',
                '.tox', 'dist', 'build', '.pytest_cache', '.mypy_cache',
                'target', '.idea', '.vscode'
            }]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in LANGUAGE_MAP:
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, directory)
                    module = os.path.dirname(rel_path).replace(os.sep, '.') or '__root__'
                    language = LANGUAGE_MAP[ext]

                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.splitlines()
                            line_count = len(lines)

                            # Calculate code vs comment vs blank lines
                            comment_lines = 0
                            blank_lines = 0
                            code_lines = 0

                            if language == 'python':
                                for line in lines:
                                    stripped = line.strip()
                                    if not stripped:
                                        blank_lines += 1
                                    elif stripped.startswith('#'):
                                        comment_lines += 1
                                    else:
                                        code_lines += 1
                            else:
                                for line in lines:
                                    stripped = line.strip()
                                    if not stripped:
                                        blank_lines += 1
                                    elif stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                                        comment_lines += 1
                                    else:
                                        code_lines += 1

                        file_info = {
                            "path": rel_path,
                            "module": module,
                            "language": language,
                            "lines": line_count,
                            "code_lines": code_lines,
                            "comment_lines": comment_lines,
                            "blank_lines": blank_lines,
                            "comment_ratio": round(comment_lines / line_count, 2) if line_count > 0 else 0,
                            "size_bytes": os.path.getsize(filepath)
                        }

                        structure["files"].append(file_info)
                        structure["modules"][module].append(file)
                        structure["total_lines"] += line_count
                        structure["total_files"] += 1
                        structure["languages"][language]["count"] += 1
                        structure["languages"][language]["lines"] += line_count

                        if line_count > structure["max_file_size"]:
                            structure["max_file_size"] = line_count

                        if line_count > 500:
                            structure["largest_files"].append({
                                "path": rel_path,
                                "lines": line_count,
                                "language": language
                            })
                    except:
                        pass

        structure["largest_files"].sort(key=lambda x: x["lines"], reverse=True)
        structure["languages"] = dict(structure["languages"])
        structure["modules"] = dict(structure["modules"])

        _analysis_cache['file_structure'] = structure
        return structure
    except Exception as e:
        return {"error": str(e)}


def identify_modules(directory: str) -> dict:
    """
    Identifies logical modules, their boundaries, and architectural roles

    Args:
        directory: Path to the code directory

    Returns:
        Dict with module organization, architectural classification, and debt hotspots
    """
    # Get cached data or compute fresh
    structure = _analysis_cache.get('file_structure')
    if not structure:
        structure = analyze_file_structure(directory)

    imports_data = _analysis_cache.get('imports')
    coupling = _analysis_cache.get('coupling')

    modules = defaultdict(lambda: {
        "files": [],
        "exports": [],
        "imports": [],
        "size": 0,
        "code_lines": 0,
        "comment_lines": 0,
        "languages": set(),
        "is_service": False,
        "is_utility": False,
        "is_core": False,
        "is_api": False,
        "is_data": False,
        "is_test": False
    })

    # Categorize files by module
    for file_info in structure.get('files', []):
        module = file_info['module']
        modules[module]["files"].append(file_info['path'])
        modules[module]["size"] += file_info['lines']
        modules[module]["code_lines"] += file_info['code_lines']
        modules[module]["comment_lines"] += file_info['comment_lines']
        modules[module]["languages"].add(file_info['language'])

    # Classify modules based on naming and structure
    for module_name, module_info in modules.items():
        module_lower = module_name.lower()
        files_lower = ' '.join(f.lower() for f in module_info["files"])

        # Service: has multiple files, handles external concerns
        if len(module_info["files"]) > 3:
            module_info["is_service"] = True

        # API layer
        if any(k in module_lower for k in ['api', 'route', 'endpoint', 'controller', 'view', 'handler']):
            module_info["is_api"] = True
            module_info["is_service"] = True

        # Data layer
        if any(k in module_lower for k in ['model', 'schema', 'entity', 'data', 'db', 'repository', 'dao']):
            module_info["is_data"] = True

        # Test module
        if any(k in module_lower for k in ['test', 'spec', 'mock']):
            module_info["is_test"] = True

        # Utility: small, no dependencies, helper functions
        if module_info["size"] < 500 and not module_info["is_service"] and not module_info["is_api"]:
            if any(k in module_lower for k in ['util', 'helper', 'common', 'shared', 'lib']):
                module_info["is_utility"] = True

        # Core: everything depends on it (detected via coupling if available)
        if coupling:
            reverse_deps = sum(1 for c in coupling.get('couplings', []) if c['to'] == module_name)
            if reverse_deps > 5:
                module_info["is_core"] = True
        else:
            # Heuristic: small modules with generic names often are core
            if any(k in module_lower for k in ['core', 'base', 'config', 'common']) and module_info["size"] < 2000:
                module_info["is_core"] = True

    # Identify debt hotspots
    debt_hotspots = []
    for module_name, module_info in modules.items():
        debt_score = 0
        issues = []

        if len(module_info["files"]) > 10:
            debt_score += 3
            issues.append("large_module")

        if module_info["size"] > 5000:
            debt_score += 3
            issues.append("too_many_lines")

        comment_ratio = module_info["comment_lines"] / module_info["size"] if module_info["size"] > 0 else 0
        if comment_ratio < 0.05 and module_info["size"] > 200:
            debt_score += 2
            issues.append("low_comment_coverage")

        if coupling:
            incoming_deps = sum(1 for c in coupling.get('couplings', []) if c['to'] == module_name)
            outgoing_deps = sum(1 for c in coupling.get('couplings', []) if c['from'] == module_name)

            if incoming_deps > 8:
                debt_score += 2
                issues.append("many_dependents")

            if outgoing_deps > 8:
                debt_score += 1
                issues.append("high_outgoing_coupling")

            # Instability = outgoing / (incoming + outgoing)
            total_deps = incoming_deps + outgoing_deps
            if total_deps > 0:
                instability = outgoing_deps / total_deps
                module_info["instability"] = round(instability, 2)
                module_info["incoming_deps"] = incoming_deps
                module_info["outgoing_deps"] = outgoing_deps

        if debt_score > 0:
            debt_hotspots.append({
                "module": module_name,
                "debt_score": debt_score,
                "issues": issues,
                "file_count": len(module_info["files"]),
                "total_lines": module_info["size"]
            })

    # Convert sets to lists for JSON serialization
    for module_info in modules.values():
        module_info["languages"] = list(module_info["languages"])

    result = {
        "modules": dict(modules),
        "total_modules": len(modules),
        "debt_hotspots": sorted(debt_hotspots, key=lambda x: x['debt_score'], reverse=True),
        "service_modules": [k for k, v in modules.items() if v["is_service"]],
        "utility_modules": [k for k, v in modules.items() if v["is_utility"]],
        "core_modules": [k for k, v in modules.items() if v["is_core"]],
        "api_modules": [k for k, v in modules.items() if v["is_api"]],
        "data_modules": [k for k, v in modules.items() if v["is_data"]],
        "test_modules": [k for k, v in modules.items() if v["is_test"]]
    }

    _analysis_cache['modules'] = result
    return result


def calculate_code_metrics(directory: str) -> dict:
    """
    Calculates comprehensive code quality metrics across the codebase

    Args:
        directory: Path to the code directory

    Returns:
        Dict with LOC metrics, complexity indicators, and quality scores
    """
    metrics = {
        "total_lines": 0,
        "total_code_lines": 0,
        "total_comment_lines": 0,
        "total_blank_lines": 0,
        "total_files": 0,
        "avg_file_size": 0,
        "avg_comment_ratio": 0,
        "duplication_candidates": [],
        "complexity_indicators": {
            "deep_nesting_count": 0,
            "long_functions": 0,
            "many_branches": 0
        }
    }

    all_lines = []

    try:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, directory)

                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            source = f.read()

                        lines = source.splitlines()
                        code_lines = 0
                        comment_lines = 0
                        blank_lines = 0

                        for line in lines:
                            stripped = line.strip()
                            if not stripped:
                                blank_lines += 1
                            elif stripped.startswith('#'):
                                comment_lines += 1
                            else:
                                code_lines += 1

                        metrics["total_lines"] += len(lines)
                        metrics["total_code_lines"] += code_lines
                        metrics["total_comment_lines"] += comment_lines
                        metrics["total_blank_lines"] += blank_lines
                        metrics["total_files"] += 1

                        all_lines.extend(lines)

                        # AST-based complexity indicators
                        try:
                            tree = ast.parse(source, filepath)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    if hasattr(node, 'end_lineno') and node.end_lineno:
                                        func_len = node.end_lineno - node.lineno
                                        if func_len > 50:
                                            metrics["complexity_indicators"]["long_functions"] += 1

                                    # Count branches
                                    branches = sum(1 for n in ast.walk(node) if isinstance(n, (ast.If, ast.While, ast.For)))
                                    if branches > 10:
                                        metrics["complexity_indicators"]["many_branches"] += 1
                        except:
                            pass
                    except:
                        pass

        if metrics["total_files"] > 0:
            metrics["avg_file_size"] = round(metrics["total_lines"] / metrics["total_files"], 2)

        if metrics["total_lines"] > 0:
            metrics["avg_comment_ratio"] = round(metrics["total_comment_lines"] / metrics["total_lines"], 2)

        # Simple duplication detection (exact line matches across files)
        line_counts = defaultdict(int)
        for line in all_lines:
            stripped = line.strip()
            if len(stripped) > 20 and not stripped.startswith('#') and not stripped.startswith('import') and not stripped.startswith('from'):
                line_counts[stripped] += 1

        duplicates = {k: v for k, v in line_counts.items() if v > 3}
        if duplicates:
            metrics["duplication_candidates"] = [
                {"code": k[:100], "occurrences": v} 
                for k, v in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

        # Overall quality score (0-100)
        quality_score = 100
        if metrics["avg_comment_ratio"] < 0.05:
            quality_score -= 15
        if metrics["complexity_indicators"]["long_functions"] > 5:
            quality_score -= 10
        if metrics["duplication_candidates"]:
            quality_score -= 10
        if metrics["avg_file_size"] > 400:
            quality_score -= 5

        metrics["quality_score"] = max(0, quality_score)
        metrics["quality_rating"] = (
            "A" if quality_score >= 90 else
            "B" if quality_score >= 75 else
            "C" if quality_score >= 60 else
            "D" if quality_score >= 40 else "F"
        )

        _analysis_cache['code_metrics'] = metrics
        return metrics
    except Exception as e:
        return {"error": str(e)}


def detect_architectural_issues(directory: str) -> dict:
    """
    Detects architectural issues like layering violations, cyclic dependencies, and god modules

    Args:
        directory: Path to the code directory

    Returns:
        Dict with architectural issues, layer violations, and refactoring recommendations
    """
    issues = []

    modules_data = _analysis_cache.get('modules')
    if not modules_data:
        modules_data = identify_modules(directory)

    imports_data = _analysis_cache.get('imports')

    # Check for layering violations
    api_modules = set(modules_data.get('api_modules', []))
    data_modules = set(modules_data.get('data_modules', []))
    core_modules = set(modules_data.get('core_modules', []))

    if imports_data and imports_data.get('imports'):
        imports_dict = imports_data['imports']

        for module, deps in imports_dict.items():
            module_base = module.split('.')[0] if '.' in module else module

            for internal_dep in deps.get('internal', []):
                dep_base = internal_dep.split('.')[0] if '.' in internal_dep else internal_dep

                # Data layer should not depend on API layer
                if module_base in data_modules and dep_base in api_modules:
                    issues.append({
                        "type": "layer_violation",
                        "severity": "high",
                        "from": module,
                        "to": internal_dep,
                        "message": f"Data layer module '{module}' imports API layer '{internal_dep}'",
                        "suggestion": "Move shared interfaces to core/utility layer or use dependency inversion"
                    })

                # Core should not depend on service modules
                if module_base in core_modules and dep_base not in core_modules and dep_base not in data_modules:
                    if dep_base not in api_modules:
                        issues.append({
                            "type": "layer_violation",
                            "severity": "medium",
                            "from": module,
                            "to": internal_dep,
                            "message": f"Core module '{module}' imports service module '{internal_dep}'",
                            "suggestion": "Refactor to keep core layer independent"
                        })

    # Check for god modules
    for module_name, module_info in modules_data.get('modules', {}).items():
        if len(module_info.get('files', [])) > 15:
            issues.append({
                "type": "god_module",
                "severity": "high",
                "module": module_name,
                "file_count": len(module_info['files']),
                "message": f"Module '{module_name}' has {len(module_info['files'])} files",
                "suggestion": "Split into smaller, cohesive sub-modules"
            })

        if module_info.get('size', 0) > 8000:
            issues.append({
                "type": "god_module",
                "severity": "medium",
                "module": module_name,
                "total_lines": module_info['size'],
                "message": f"Module '{module_name}' exceeds 8000 lines",
                "suggestion": "Extract components into separate modules"
            })

    # Check for test coverage indicators
    test_modules = set(modules_data.get('test_modules', []))
    non_test_modules = set(modules_data.get('modules', {}).keys()) - test_modules

    if non_test_modules and not test_modules:
        issues.append({
            "type": "missing_tests",
            "severity": "high",
            "message": "No test modules detected in the codebase",
            "suggestion": "Add unit and integration tests for critical modules"
        })
    elif len(test_modules) < len(non_test_modules) * 0.2:
        issues.append({
            "type": "insufficient_tests",
            "severity": "medium",
            "message": f"Low test module ratio: {len(test_modules)} test modules for {len(non_test_modules)} source modules",
            "suggestion": "Increase test coverage, especially for core and API modules"
        })

    result = {
        "issues": sorted(issues, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['severity'], 3)),
        "total_issues": len(issues),
        "high_severity": len([i for i in issues if i['severity'] == 'high']),
        "medium_severity": len([i for i in issues if i['severity'] == 'medium']),
        "low_severity": len([i for i in issues if i['severity'] == 'low'])
    }

    _analysis_cache['architectural_issues'] = result
    return result