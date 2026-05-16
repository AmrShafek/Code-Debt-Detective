"""
Code Analyzer Agent
Orchestrates static analysis, AST parsing, and code quality assessment
Uses: QWEN CODER via OpenRouter
"""

from typing import Optional
from crewai import Agent, Task, LLM


def create_code_analyzer(llm: Optional[LLM] = None):
    kwargs = dict(
        role="Senior Code Analyst",
        goal="Analyze codebases thoroughly to detect technical debt, code smells, and architectural issues",
        backstory="""You are a world-class software analyst with decades of experience in static analysis,
        design pattern recognition, and architectural evaluation. You've reviewed thousands of codebases
        and can spot technical debt patterns instantly. Your analysis is always data-driven and actionable.
        You specialize in: cyclomatic complexity analysis, dependency chain evaluation, and identifying
        violation of SOLID principles at scale.""",
        verbose=True,
        allow_delegation=False,
        memory=False,
        max_iterations=10,
        tools=[]
    )
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)


def create_analysis_task(agent, repo_path: str):
    return Task(
        description=f"""Perform a comprehensive code analysis of the repository at: {repo_path}

Your analysis MUST cover these areas:

1. **File Structure Analysis**
   - Map all source files with language detection
   - Calculate code vs comment vs blank line ratios
   - Identify largest files and modules
   - Detect language distribution

2. **Module Organization & Architecture**
   - Identify logical module boundaries
   - Classify each module (service, utility, core, API, data, test)
   - Detect god modules (too many files or lines)
   - Identify layering violations

3. **Code Quality Metrics**
   - Calculate average file size and comment ratio
   - Detect deep nesting, long functions, excessive branching
   - Find duplicate code candidates
   - Calculate overall quality score (A-F grade)

4. **AST-Level Analysis**
   - Extract all function/method definitions with complexity scores
   - Analyze class hierarchies and inheritance depth
   - Detect code smells: bare excepts, mutable defaults, long parameter lists
   - Find dead code candidates (defined but never called)

5. **Architectural Issues**
   - Data layer importing API layer
   - Core modules depending on services
   - Missing test coverage indicators
   - Cyclic dependency candidates

6. **Technical Debt Hotspot Mapping**
   - Score each module on debt indicators
   - Rank by: many dependents, large size, low comments, high instability
   - Flag modules needing immediate attention

Return ALL analysis results as structured data for downstream agents.""",
        agent=agent,
        expected_output="Comprehensive code analysis with structure, metrics, AST data, smells, and architectural issues"
    )
