"""
Refactoring Strategist Agent
Plans safe, phased refactoring with clear milestones
Uses: DEEPSEEK via OpenRouter
"""

from typing import Optional
from crewai import Agent, Task, LLM


def create_refactoring_strategist(llm: Optional[LLM] = None):
    kwargs = dict(
        role="Refactoring Strategy Lead",
        goal="Create a practical, phased refactoring plan that minimizes disruption while maximizing impact",
        backstory="""You are an expert in software refactoring with a perfect track record of 
        delivering safe migrations in enterprise systems. You understand that refactoring must be 
        done incrementally, with clear milestones and rollback points.
        You prioritize based on: risk mitigation first, then impact, then effort.
        You always consider team capacity and business constraints.""",
        verbose=True,
        allow_delegation=False,
        memory=False,
        max_iterations=7
    )
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)


def create_refactoring_strategy_task(agent, analysis_data):
    return Task(
        description=f"""Based on this code analysis:
{analysis_data}

Create a detailed, practical refactoring plan with these constraints:

1. **Phase Design**
   - Split into 3-6 phases (each 1-2 weeks of team effort)
   - Each phase must be independently shippable
   - Earlier phases should have ZERO risk
   - Later phases can have higher risk as team gains confidence

2. **Phase Structure**
   For each phase:
   - What modules to extract or refactor
   - Which tests must pass before proceeding
   - Expected team effort (days)
   - Risk level (LOW, MEDIUM, HIGH)
   - Success criteria
   - Rollback procedure

3. **Priority Scoring**
   Score each extraction opportunity on:
   - Effort (1-10)
   - Risk (1-10)
   - Impact (1-10, how much debt it removes)
   - Dependencies (number of reverse-dependencies)
   
   Formula: Priority = (Impact × 2 - Effort) / Risk

4. **Safety Measures**
   - Identify which tests provide coverage
   - Flag breaking API changes
   - Note integration points that need special care
   - Suggest monitoring/canary approaches

5. **Deliverables**
   Output a structured JSON:
   ```json
   {{
     "refactoring_phases": [
       {{
         "phase": 1,
         "name": "Extract shared utilities",
         "duration_days": 5,
         "risk_level": "LOW",
         "modules_to_extract": ["common_utils"],
         "breaking_changes": [],
         "test_coverage_required": "100%",
         "success_criteria": [
           "All tests pass",
           "No increase in coupling",
           "0 regressions in staging"
         ],
         "rollback_plan": "Revert commit, restore from backup",
         "dependencies": ["setup_dev_env", "test_infra"],
         "team_capacity_required": "2 engineers"
       }}
     ],
     "extraction_opportunities": [
       {{
         "module": "shared_models",
         "effort_score": 3,
         "risk_score": 2,
         "impact_score": 8,
         "priority_rank": 1,
         "affected_modules": ["service_a", "service_b"],
         "reverse_dependencies": 6,
         "estimated_value": "High - removes circular dependency"
       }}
     ],
     "critical_path": ["Phase 1", "Phase 2"],
     "total_effort_days": 30
   }}
   ```

Be specific about module names and actual pain points you see in the analysis.
Avoid generic advice—this plan must be immediately actionable.""",
        agent=agent,
        expected_output="Detailed refactoring roadmap with phased approach, priorities, risks, and success criteria"
    )
