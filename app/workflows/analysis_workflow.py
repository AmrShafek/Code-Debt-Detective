"""
Analysis Workflow
Orchestrates the full multi-agent code analysis pipeline
"""

from typing import Dict, Any, Optional
import json
from pathlib import Path

from app.agents.code_analyzer_agent import create_code_analyzer, create_analysis_task
from app.tools.code_analysis_tools import (
    analyze_file_structure,
    identify_modules,
    calculate_code_metrics,
    detect_architectural_issues
)
from app.tools.ast_tools import (
    extract_functions,
    extract_classes,
    find_code_smells,
    get_function_dependencies
)
from app.tools.dependency_graph_tools import (
    extract_imports,
    build_dependency_matrix,
    detect_cyclic_dependencies,
    calculate_coupling_metrics,
    build_dependency_graph_json
)
from app.tools.git_tools import (
    get_git_history,
    detect_churn,
    analyze_commit_patterns
)


class AnalysisWorkflow:
    """Orchestrates the full multi-agent code analysis pipeline"""

    def __init__(self, repo_path: str, use_llm: bool = True):
        self.repo_path = Path(repo_path)
        self.use_llm = use_llm
        self.results = {}
        self.agent = None

    async def run_full_analysis(self) -> Dict[str, Any]:
        """Run the complete analysis pipeline"""
        self.results["file_structure"] = analyze_file_structure(str(self.repo_path))
        self.results["imports"] = extract_imports(str(self.repo_path))

        if "error" not in self.results["file_structure"]:
            self.results["modules"] = identify_modules(str(self.repo_path))
            self.results["code_metrics"] = calculate_code_metrics(str(self.repo_path))

            if self.results["imports"] and "error" not in self.results["imports"]:
                self.results["dependency_matrix"] = build_dependency_matrix(str(self.repo_path))
                self.results["cyclic_dependencies"] = detect_cyclic_dependencies(str(self.repo_path))
                self.results["coupling_metrics"] = calculate_coupling_metrics(str(self.repo_path))
                self.results["graph_json"] = build_dependency_graph_json(str(self.repo_path))

            self.results["functions"] = extract_functions(str(self.repo_path))
            self.results["classes"] = extract_classes(str(self.repo_path))
            self.results["code_smells"] = find_code_smells(str(self.repo_path))
            self.results["function_deps"] = get_function_dependencies(str(self.repo_path))
            self.results["architectural_issues"] = detect_architectural_issues(str(self.repo_path))

            git_data = get_git_history(str(self.repo_path), max_commits=50)
            if "error" not in git_data:
                self.results["git_history"] = git_data
                self.results["churn"] = detect_churn(str(self.repo_path))
                self.results["commit_patterns"] = analyze_commit_patterns(str(self.repo_path))
        else:
            self.results["error"] = self.results["file_structure"]["error"]

        if self.use_llm and "error" not in self.results:
            await self._run_llm_analysis()

        return self._build_report()

    async def _run_llm_analysis(self):
        """Run CrewAI agent analysis on collected data"""
        try:
            self.agent = create_code_analyzer()
            analysis_summary = json.dumps({
                "file_count": self.results.get("file_structure", {}).get("total_files"),
                "total_lines": self.results.get("file_structure", {}).get("total_lines"),
                "quality_score": self.results.get("code_metrics", {}).get("quality_score"),
                "quality_rating": self.results.get("code_metrics", {}).get("quality_rating"),
                "smell_count": self.results.get("code_smells", {}).get("total_smells"),
                "arch_issues": self.results.get("architectural_issues", {}).get("total_issues"),
                "cycle_count": self.results.get("cyclic_dependencies", {}).get("total_cycles"),
            }, indent=2)

            task = create_analysis_task(self.agent, str(self.repo_path))
            crew_result = task.agent.execute_task(task)
            self.results["llm_analysis"] = crew_result
        except Exception as e:
            self.results["llm_analysis"] = {"error": str(e)}

    def _build_report(self) -> Dict[str, Any]:
        """Build the final analysis report"""
        fs = self.results.get("file_structure", {})
        cm = self.results.get("code_metrics", {})
        cs = self.results.get("code_smells", {})
        ai = self.results.get("architectural_issues", {})
        cd = self.results.get("cyclic_dependencies", {})
        funcs = self.results.get("functions", {})
        classes = self.results.get("classes", {})

        return {
            "repo_path": str(self.repo_path),
            "summary": {
                "total_files": fs.get("total_files", 0),
                "total_lines": fs.get("total_lines", 0),
                "languages": fs.get("languages", {}),
                "quality_score": cm.get("quality_score", 0),
                "quality_rating": cm.get("quality_rating", "N/A"),
                "total_smells": cs.get("total_smells", 0),
                "critical_smells": cs.get("critical_count", 0),
                "arch_issues": ai.get("total_issues", 0),
                "high_severity_arch": ai.get("high_severity", 0),
                "cycles": cd.get("total_cycles", 0),
                "total_functions": funcs.get("total_functions", 0),
                "total_classes": classes.get("total_classes", 0),
                "avg_complexity": funcs.get("avg_complexity", 0),
            },
            "details": self.results,
            "llm_analysis": self.results.get("llm_analysis")
        }

    def get_results(self) -> Dict[str, Any]:
        return self.results

    def get_graph_data(self) -> Optional[Dict[str, Any]]:
        return self.results.get("graph_json")

    def get_debt_hotspots(self) -> list:
        modules = self.results.get("modules", {})
        return modules.get("debt_hotspots", [])
