"""
Code Debt Detective - Main Entry Point
AI-powered multi-agent system for analyzing software repositories
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings


def main():
    settings.ensure_dirs()
    print(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"LLM Provider: {settings.LLM_PROVIDER.upper()} ({settings.LLM_MODEL})")

    try:
        import streamlit.web.bootstrap
        from app.gui.app import main as gui_main

        gui_path = Path(__file__).parent / "gui" / "app.py"
        sys.argv = ["streamlit", "run", str(gui_path)]
        streamlit.web.bootstrap.run(
            str(gui_path),
            None,
            [],
            flag_options={}
        )
    except ImportError:
        print("Streamlit not available. Run: pip install streamlit")
        sys.exit(1)


def run_cli():
    """Run CLI-based analysis without GUI"""
    import argparse

    parser = argparse.ArgumentParser(description="Code Debt Detective CLI")
    parser.add_argument("path", help="Path to repository to analyze")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM analysis")

    args = parser.parse_args()

    async def analyze():
        from app.workflows.analysis_workflow import AnalysisWorkflow
        workflow = AnalysisWorkflow(args.path, use_llm=not args.no_llm)
        result = await workflow.run_full_analysis()
        import json
        print(json.dumps(result, indent=2, default=str))

    asyncio.run(analyze())


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        main()
