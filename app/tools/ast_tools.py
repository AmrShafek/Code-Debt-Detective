"""
AST Analysis Tools
Provides Abstract Syntax Tree parsing and code structure analysis for CrewAI agents
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from collections import defaultdict

# Shared analysis cache for inter-agent communication
_analysis_cache = {}


def parse_ast_tree(file_path: str) -> dict:
    """
    Parse a Python file into an Abstract Syntax Tree (AST)

    Args:
        file_path: Absolute or relative path to the Python file

    Returns:
        Dict with AST metadata, parsing status, and top-level node counts
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=file_path)

        node_counts = defaultdict(int)
        for node in ast.walk(tree):
            node_counts[type(node).__name__] += 1

        result = {
            "file": file_path,
            "parsed": True,
            "total_nodes": len(list(ast.walk(tree))),
            "node_distribution": dict(node_counts),
            "lines_of_code": len(source.splitlines()),
            "ast_dump": ast.dump(tree, annotate_fields=False, include_attributes=False)
        }

        _analysis_cache[f'ast_{file_path}'] = result
        return result
    except SyntaxError as e:
        return {
            "file": file_path,
            "parsed": False,
            "error": f"SyntaxError at line {e.lineno}: {e.msg}",
            "text": e.text
        }
    except Exception as e:
        return {"file": file_path, "parsed": False, "error": str(e)}


def extract_functions(directory: str, include_metrics: bool = True) -> dict:
    """
    Extract all function and method definitions from Python files with optional complexity metrics

    Args:
        directory: Path to the code directory
        include_metrics: If True, calculate cyclomatic complexity and line counts

    Returns:
        Dict with function inventory, complexity scores, and nested structure
    """
    functions = []

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

                        tree = ast.parse(source, filepath)
                        lines = source.splitlines()

                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                func_info = {
                                    "file": rel_path,
                                    "name": node.name,
                                    "line_start": node.lineno,
                                    "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                                    "is_method": False,
                                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                                    "decorators": [ast.dump(d) for d in node.decorator_list],
                                    "args_count": len(node.args.args) + len(node.args.kwonlyargs),
                                    "has_varargs": node.args.vararg is not None,
                                    "has_kwargs": node.args.kwarg is not None,
                                    "returns_annotation": ast.dump(node.returns) if node.returns else None
                                }

                                if include_metrics:
                                    func_lines = lines[node.lineno-1:node.end_lineno] if hasattr(node, 'end_lineno') else []
                                    func_info["line_count"] = len(func_lines)
                                    func_info["cyclomatic_complexity"] = _calculate_cyclomatic_complexity(node)
                                    func_info["cognitive_complexity"] = _calculate_cognitive_complexity(node)
                                    func_info["is_long_method"] = len(func_lines) > 50
                                    func_info["is_complex"] = func_info["cyclomatic_complexity"] > 10
                                    func_info["has_nested_functions"] = any(
                                        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) 
                                        for n in ast.walk(node) if n != node
                                    )

                                functions.append(func_info)

                            elif isinstance(node, ast.ClassDef):
                                for item in node.body:
                                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        method_info = {
                                            "file": rel_path,
                                            "name": f"{node.name}.{item.name}",
                                            "class": node.name,
                                            "line_start": item.lineno,
                                            "line_end": item.end_lineno if hasattr(item, 'end_lineno') else item.lineno,
                                            "is_method": True,
                                            "is_async": isinstance(item, ast.AsyncFunctionDef),
                                            "decorators": [ast.dump(d) for d in item.decorator_list],
                                            "args_count": len(item.args.args) + len(item.args.kwonlyargs) - 1,  # exclude self/cls
                                            "is_property": any(
                                                isinstance(d, ast.Name) and d.id == 'property' 
                                                for d in item.decorator_list
                                            ),
                                            "is_staticmethod": any(
                                                isinstance(d, ast.Name) and d.id == 'staticmethod' 
                                                for d in item.decorator_list
                                            ),
                                            "is_classmethod": any(
                                                isinstance(d, ast.Name) and d.id == 'classmethod' 
                                                for d in item.decorator_list
                                            )
                                        }

                                        if include_metrics:
                                            method_lines = lines[item.lineno-1:item.end_lineno] if hasattr(item, 'end_lineno') else []
                                            method_info["line_count"] = len(method_lines)
                                            method_info["cyclomatic_complexity"] = _calculate_cyclomatic_complexity(item)
                                            method_info["cognitive_complexity"] = _calculate_cognitive_complexity(item)
                                            method_info["is_long_method"] = len(method_lines) > 50
                                            method_info["is_complex"] = method_info["cyclomatic_complexity"] > 10

                                        functions.append(method_info)
                    except:
                        pass

        # Identify hotspots
        complex_functions = [f for f in functions if f.get("is_complex", False)]
        long_functions = [f for f in functions if f.get("is_long_method", False)]

        result = {
            "functions": functions,
            "total_functions": len(functions),
            "complex_functions": sorted(complex_functions, key=lambda x: x.get("cyclomatic_complexity", 0), reverse=True),
            "long_functions": sorted(long_functions, key=lambda x: x.get("line_count", 0), reverse=True),
            "avg_complexity": round(
                sum(f.get("cyclomatic_complexity", 0) for f in functions) / len(functions), 2
            ) if functions else 0,
            "files_analyzed": len(set(f["file"] for f in functions))
        }

        _analysis_cache['functions'] = result
        return result
    except Exception as e:
        return {"error": str(e)}


def extract_classes(directory: str) -> dict:
    """
    Extract all class definitions from Python files with inheritance and composition analysis

    Args:
        directory: Path to the code directory

    Returns:
        Dict with class inventory, inheritance tree, and composition patterns
    """
    classes = []
    inheritance_map = defaultdict(list)

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

                        tree = ast.parse(source, filepath)

                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                bases = []
                                for base in node.bases:
                                    if isinstance(base, ast.Name):
                                        bases.append(base.id)
                                    elif isinstance(base, ast.Attribute):
                                        bases.append(f"{ast.dump(base.value)}.{base.attr}")
                                    else:
                                        bases.append(ast.dump(base))

                                methods = []
                                attributes = []
                                class_attributes = []

                                for item in node.body:
                                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        methods.append(item.name)
                                    elif isinstance(item, ast.Assign):
                                        for target in item.targets:
                                            if isinstance(target, ast.Name):
                                                class_attributes.append(target.id)
                                    elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                        class_attributes.append(item.target.id)

                                # Detect composition via instance attributes in __init__
                                init_method = next((item for item in node.body 
                                                    if isinstance(item, ast.FunctionDef) and item.name == '__init__'), None)
                                if init_method:
                                    for stmt in ast.walk(init_method):
                                        if isinstance(stmt, ast.Assign):
                                            for target in stmt.targets:
                                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                                    attributes.append(target.attr)

                                class_info = {
                                    "file": rel_path,
                                    "name": node.name,
                                    "line_start": node.lineno,
                                    "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                                    "bases": bases,
                                    "methods": methods,
                                    "method_count": len(methods),
                                    "attributes": list(set(attributes)),
                                    "class_attributes": class_attributes,
                                    "decorators": [ast.dump(d) for d in node.decorator_list],
                                    "is_dataclass": any(
                                        isinstance(d, ast.Name) and d.id == 'dataclass' 
                                        for d in node.decorator_list
                                    ),
                                    "docstring": ast.get_docstring(node)
                                }

                                classes.append(class_info)

                                for base in bases:
                                    inheritance_map[base].append(node.name)
                    except:
                        pass

        # Detect deep inheritance hierarchies
        deep_hierarchies = [c for c in classes if len(c["bases"]) > 1 or any(len(inheritance_map.get(c["name"], [])) > 3 for _ in [c])]

        result = {
            "classes": classes,
            "total_classes": len(classes),
            "inheritance_map": dict(inheritance_map),
            "deep_hierarchies": deep_hierarchies,
            "dataclasses": [c["name"] for c in classes if c["is_dataclass"]],
            "avg_methods_per_class": round(
                sum(c["method_count"] for c in classes) / len(classes), 2
            ) if classes else 0,
            "god_classes": [c for c in classes if c["method_count"] > 20]
        }

        _analysis_cache['classes'] = result
        return result
    except Exception as e:
        return {"error": str(e)}


def find_code_smells(directory: str) -> dict:
    """
    Detect common code smells and anti-patterns in Python code

    Args:
        directory: Path to the code directory

    Returns:
        Dict with detected code smells categorized by severity
    """
    smells = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }

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

                        tree = ast.parse(source, filepath)
                        lines = source.splitlines()

                        # Check for bare except clauses
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ExceptHandler):
                                if node.type is None:
                                    smells["critical"].append({
                                        "type": "bare_except",
                                        "file": rel_path,
                                        "line": node.lineno,
                                        "message": "Bare except clause catches SystemExit and KeyboardInterrupt",
                                        "suggestion": "Use 'except Exception:' instead"
                                    })

                            # Check for mutable default arguments
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                for default in node.args.defaults + node.args.kw_defaults:
                                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                                        smells["high"].append({
                                            "type": "mutable_default",
                                            "file": rel_path,
                                            "line": node.lineno,
                                            "function": node.name,
                                            "message": f"Mutable default argument in function '{node.name}'",
                                            "suggestion": "Use None as default and initialize mutable object inside function"
                                        })

                            # Check for deeply nested blocks
                            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                                depth = _get_nesting_depth(node)
                                if depth > 4:
                                    smells["medium"].append({
                                        "type": "deep_nesting",
                                        "file": rel_path,
                                        "line": node.lineno,
                                        "depth": depth,
                                        "message": f"Deeply nested block (depth: {depth})",
                                        "suggestion": "Extract nested logic into separate functions"
                                    })

                            # Check for long parameter lists
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                total_params = len(node.args.args) + len(node.args.kwonlyargs) + len(node.args.defaults)
                                if total_params > 7:
                                    smells["medium"].append({
                                        "type": "long_parameter_list",
                                        "file": rel_path,
                                        "line": node.lineno,
                                        "function": node.name,
                                        "param_count": total_params,
                                        "message": f"Function '{node.name}' has {total_params} parameters",
                                        "suggestion": "Consider using a data class or kwargs pattern"
                                    })

                            # Check for duplicate string literals
                            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) > 5:
                                # This is simplified; real implementation would track across files
                                pass

                        # Check file-level smells
                        if len(lines) > 1000:
                            smells["medium"].append({
                                "type": "large_file",
                                "file": rel_path,
                                "lines": len(lines),
                                "message": f"File has {len(lines)} lines",
                                "suggestion": "Consider splitting into smaller modules"
                            })

                        # Check for TODO/FIXME comments
                        for i, line in enumerate(lines, 1):
                            if 'TODO' in line.upper() or 'FIXME' in line.upper() or 'HACK' in line.upper():
                                smells["low"].append({
                                    "type": "todo_comment",
                                    "file": rel_path,
                                    "line": i,
                                    "message": f"Found technical debt comment: {line.strip()}",
                                    "suggestion": "Address or ticket the technical debt item"
                                })
                    except:
                        pass

        result = {
            "smells": smells,
            "total_smells": sum(len(v) for v in smells.values()),
            "critical_count": len(smells["critical"]),
            "high_count": len(smells["high"]),
            "medium_count": len(smells["medium"]),
            "low_count": len(smells["low"])
        }

        _analysis_cache['code_smells'] = result
        return result
    except Exception as e:
        return {"error": str(e)}


def get_function_dependencies(directory: str) -> dict:
    """
    Analyze function-level call dependencies within the codebase

    Args:
        directory: Path to the code directory

    Returns:
        Dict with call graphs, dead code candidates, and entry points
    """
    call_graph = defaultdict(list)
    all_functions = set()
    called_functions = set()

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

                        tree = ast.parse(source, filepath)
                        current_function = None

                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                current_function = f"{rel_path}::{node.name}"
                                all_functions.add(current_function)

                            if isinstance(node, ast.Call) and current_function:
                                if isinstance(node.func, ast.Name):
                                    called = node.func.id
                                    call_graph[current_function].append(called)
                                    called_functions.add(called)
                                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                                    if node.func.value.id == 'self':
                                        called = f"self.{node.func.attr}"
                                    else:
                                        called = f"{node.func.value.id}.{node.func.attr}"
                                    call_graph[current_function].append(called)
                                    called_functions.add(called)
                    except:
                        pass

        # Find potentially dead code (defined but never called, excluding main/dunders)
        dead_code_candidates = []
        for func in all_functions:
            func_name = func.split("::")[-1]
            if func_name not in called_functions and not func_name.startswith('__') and func_name != 'main':
                dead_code_candidates.append(func)

        result = {
            "call_graph": dict(call_graph),
            "all_functions": list(all_functions),
            "called_functions": list(called_functions),
            "dead_code_candidates": dead_code_candidates,
            "entry_points": [f for f in all_functions if f.split("::")[-1] in ('main', 'run', 'start', 'execute')]
        }

        _analysis_cache['function_dependencies'] = result
        return result
    except Exception as e:
        return {"error": str(e)}


# Helper functions (not exposed as tools)
def _calculate_cyclomatic_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity for a function/method node"""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            complexity += 1
    return complexity


def _calculate_cognitive_complexity(node: ast.AST) -> int:
    """Calculate cognitive complexity (simplified)"""
    complexity = 0
    nesting = 0

    def walk(node, depth=0):
        nonlocal complexity, nesting
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With)):
            complexity += 1 + depth
            depth += 1
        for child in ast.iter_child_nodes(node):
            walk(child, depth)

    walk(node)
    return complexity


def _get_nesting_depth(node: ast.AST) -> int:
    """Get the nesting depth of a control flow node"""
    depth = 0
    current = node
    while hasattr(current, 'parent'):
        current = current.parent
        if isinstance(current, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            depth += 1
    return depth