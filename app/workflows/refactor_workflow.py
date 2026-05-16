"""
Refactor Workflow
Orchestrates multi-agent refactoring strategy generation, risk assessment, and diff explanation
Strategist, Risk Assessor, and Diff Explainer use DEEPSEEK via OpenRouter
"""

from typing import Dict, Any, Optional
import json
import re
from pathlib import Path

from app.agents.refactor_strategist_agent import (
    create_refactoring_strategist,
    create_refactoring_strategy_task
)
from app.agents.risk_assessor_agent import (
    create_risk_assessor,
    create_risk_assessment_task
)
from app.agents.diff_explainer_agent import (
    create_diff_explainer,
    create_diff_explanation_task
)
from app.services.llm_service import LLMService


class RefactorWorkflow:
    """Orchestrates multi-agent refactoring strategy generation"""

    def __init__(self, analysis_results: Dict[str, Any], use_llm: bool = True):
        self.analysis = analysis_results
        self.use_llm = use_llm
        self.refactoring_plan = None
        self.risk_assessment = None
        self.diff_explanation = None
        self._llm = LLMService()

    def run_full_refactoring_pipeline(self) -> Dict[str, Any]:
        """Run the complete refactoring pipeline"""
        if not self.use_llm:
            self.refactoring_plan = self._generate_local_plan()
            self.risk_assessment = self._assess_local_risk()
            self.diff_explanation = self._generate_local_explanation()
        else:
            self._run_llm_pipeline()

        return self._build_report()

    def _generate_local_plan(self) -> Dict[str, Any]:
        """Generate refactoring plan without LLM"""
        hotspots = self.analysis.get("details", {}).get("modules", {}).get("debt_hotspots", [])
        graph = self.analysis.get("details", {}).get("graph_json", {}).get("graph", {})

        phases = []
        for i, hotspot in enumerate(hotspots[:5]):
            phases.append({
                "phase": i + 1,
                "name": f"Refactor {hotspot['module']}",
                "duration_days": max(3, hotspot.get("debt_score", 1) * 2),
                "risk_level": "HIGH" if hotspot.get("debt_score", 0) > 5 else "MEDIUM",
                "modules_to_extract": [hotspot["module"]],
                "breaking_changes": [],
                "success_criteria": [
                    "All tests pass",
                    "Reduced module size by 50%",
                    "No new coupling introduced"
                ],
                "rollback_plan": "Revert the merge commit"
            })

        return {
            "refactoring_phases": phases,
            "total_effort_days": sum(p["duration_days"] for p in phases),
            "extraction_opportunities": [
                {
                    "module": h["module"],
                    "effort_score": h.get("debt_score", 5),
                    "risk_score": h.get("debt_score", 5) // 2,
                    "impact_score": h.get("debt_score", 5) * 2,
                    "priority_rank": i + 1
                }
                for i, h in enumerate(hotspots[:10])
            ]
        }

    def _assess_local_risk(self) -> Dict[str, Any]:
        """Assess risk without LLM"""
        plan = self.refactoring_plan or self._generate_local_plan()
        cycles = self.analysis.get("details", {}).get("cyclic_dependencies", {})
        quality = self.analysis.get("details", {}).get("code_metrics", {})

        assessments = []
        for phase in plan.get("refactoring_phases", []):
            assessments.append({
                "phase": phase["phase"],
                "name": phase["name"],
                "impact_score": 5,
                "probability_score": 4 if phase["risk_level"] == "HIGH" else 2,
                "detection_score": 6 if quality.get("quality_score", 50) < 60 else 8,
                "overall_risk": round(
                    (5 * 4) / max(6, 1), 2
                ),
                "blast_radius": len(cycles.get("cycles", []))
            })

        return {
            "phase_risks": assessments,
            "total_risk_score": sum(a["overall_risk"] for a in assessments),
            "has_breaking_changes": bool(cycles.get("cycles")),
            "mitigation_suggestions": [
                "Add integration tests before refactoring",
                "Use feature flags for risky changes",
                "Deploy to staging for 24h validation"
            ]
        }

    def _generate_local_explanation(self) -> Dict[str, Any]:
        """Generate diff explanation without LLM"""
        plan = self.refactoring_plan or self._generate_local_plan()
        risk = self.risk_assessment or self._assess_local_risk()

        return {
            "executive_summary": f"Refactoring plan with {len(plan.get('refactoring_phases', []))} phases "
                                 f"totaling {plan.get('total_effort_days', 0)} effort days. "
                                 f"Risk score: {risk.get('total_risk_score', 0):.1f}.",
            "phases": [
                {
                    "name": p["name"],
                    "guide": f"Phase {p['phase']}: {p['name']}\n"
                             f"Risk: {p['risk_level']}\n"
                             f"Duration: {p['duration_days']} days\n"
                             f"Modules: {', '.join(p['modules_to_extract'])}",
                    "breaking_changes": p["breaking_changes"],
                    "testing_checklist": p["success_criteria"],
                    "rollback_procedure": p["rollback_plan"]
                }
                for p in plan.get("refactoring_phases", [])
            ],
            "communication_templates": {
                "pr_template": "## Summary\nAutomated refactoring plan generated by Code Debt Detective."
            }
        }

    @staticmethod
    def _parse_json_response(text: str) -> dict | str:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        if isinstance(text, dict):
            return text
        text = str(text)
        match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
        if match:
            text = match.group(1)
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return text

    def _run_llm_pipeline(self):
        """Run the full CrewAI pipeline with DEEPSEEK for all 3 refactoring agents"""
        try:
            refactor_llm = self._llm.get_refactor_llm()
            analysis_summary = json.dumps(self.analysis.get("summary", {}), indent=2)

            strategist = create_refactoring_strategist(llm=refactor_llm)
            strategy_task = create_refactoring_strategy_task(strategist, analysis_summary)
            self.refactoring_plan = self._parse_json_response(strategist.execute_task(strategy_task))

            assessor = create_risk_assessor(llm=refactor_llm)
            risk_task = create_risk_assessment_task(assessor, analysis_summary, str(self.refactoring_plan))
            self.risk_assessment = self._parse_json_response(assessor.execute_task(risk_task))

            explainer = create_diff_explainer(llm=refactor_llm)
            explain_task = create_diff_explanation_task(
                explainer, analysis_summary,
                str(self.refactoring_plan), str(self.risk_assessment)
            )
            self.diff_explanation = self._parse_json_response(explainer.execute_task(explain_task))
        except Exception as e:
            error = {"error": str(e)}
            if not self.refactoring_plan:
                self.refactoring_plan = self._generate_local_plan()
            if not self.risk_assessment:
                self.risk_assessment = self._assess_local_risk()
            if not self.diff_explanation:
                self.diff_explanation = self._generate_local_explanation()

    def _build_report(self) -> Dict[str, Any]:
        return {
            "refactoring_plan": self.refactoring_plan,
            "risk_assessment": self.risk_assessment,
            "diff_explanation": self.diff_explanation,
            "phases": self.refactoring_plan.get("refactoring_phases", []) if isinstance(self.refactoring_plan, dict) else [],
            "total_effort_days": self.refactoring_plan.get("total_effort_days", 0) if isinstance(self.refactoring_plan, dict) else 0,
        }

    def get_refactoring_plan(self) -> Optional[Dict[str, Any]]:
        return self.refactoring_plan

    def get_risk_assessment(self) -> Optional[Dict[str, Any]]:
        return self.risk_assessment

    def get_diff_explanation(self) -> Optional[Dict[str, Any]]:
        return self.diff_explanation
