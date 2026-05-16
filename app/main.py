"""
Code Debt Detective - Main Entry Point
AI-powered multi-agent system for analyzing software repositories
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings
from app.services.llm_service import LLMService


def main():
    settings.ensure_dirs()
    llm = LLMService()
    ca = llm.get_code_analyzer_config()
    rf = llm.get_refactor_config()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Code Analyzer: {ca.get('model', 'N/A')} ({'key set' if llm.is_code_analyzer_configured() else 'no key'})")
    print(f"Refactoring Agents: {rf.get('model', 'N/A')} ({'key set' if llm.is_refactor_configured() else 'no key'})")

    gui_path = Path(__file__).parent / "gui" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(gui_path)])


def run_cli():
    """Run CLI-based analysis without GUI"""
    import argparse

    parser = argparse.ArgumentParser(description="Code Debt Detective CLI")
    parser.add_argument("path", help="Path to repository to analyze")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM analysis")

    args = parser.parse_args()

    from app.workflows.analysis_workflow import AnalysisWorkflow
    workflow = AnalysisWorkflow(args.path, use_llm=not args.no_llm)
    result = workflow.run_full_analysis()
    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        main()
