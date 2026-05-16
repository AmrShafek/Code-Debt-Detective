"""
Risk Assessor Agent
Evaluates change impact, breaking change probability, and migration safety
Uses: DEEPSEEK via OpenRouter
"""

from typing import Optional
from crewai import Agent, Task, LLM


def create_risk_assessor(llm: Optional[LLM] = None):
    kwargs = dict(
        role="Change Risk Analyst",
        goal="Assess the risk and impact of every proposed refactoring change before it happens",
        backstory="""You are a senior risk analyst who specializes in predicting refactoring failures.
        You've seen countless migrations go wrong and know exactly what signals to look for.
        You analyze dependency chains, public API surface areas, test coverage gaps, and
        integration points to calculate precise risk scores. Your risk assessments have
        prevented multiple production outages by flagging hidden dependencies early.""",
        verbose=True,
        allow_delegation=False,
        memory=False,
        max_iterations=8
    )
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)


def create_risk_assessment_task(agent, analysis_data, refactoring_plan):
    return Task(
        description=f"""Analyze the risk of the proposed refactoring plan:

CODE ANALYSIS:
{analysis_data}

REFACTORING PLAN:
{refactoring_plan}

Perform the following risk analysis:

1. **Breaking Change Detection**
   For EACH proposed change:
   - Identify all consumers of the changing API/module
   - Classify breaking vs non-breaking changes
   - Estimate migration effort for downstream teams
   - Flag changes that require coordinated deployments

2. **Dependency Impact Analysis**
   - Trace the dependency chain of each changed module
   - Identify transitive dependencies that may break
   - Calculate "blast radius" (number of affected modules)
   - Highlight tightly coupled clusters

3. **Test Coverage Risk**
   - Identify modules with insufficient test coverage
   - Flag high-risk changes in untested code
   - Suggest minimum test thresholds before refactoring
   - Identify critical paths lacking integration tests

4. **Risk Scoring**
   For each refactoring phase, calculate:
   - Impact score (1-10): how many modules affected
   - Probability score (1-10): likelihood of breaking something
   - Detection score (1-10): how easily issues will be caught
   - Overall Risk Score = Impact × Probability ÷ Detection

5. **Mitigation Strategies**
   - Recommend canary deployment patterns
   - Suggest feature flags for risky changes
   - Identify safe rollback points
   - Propose gradual migration approaches

Output structured JSON with risk scores, breaking changes list, and mitigation plans.""",
        agent=agent,
        expected_output="Risk assessment with breaking changes, blast radius, test gaps, and mitigation strategies"
    )
