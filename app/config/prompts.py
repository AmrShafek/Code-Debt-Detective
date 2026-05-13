"""
Prompt templates for LLM-based analysis fallbacks and summary generation
"""

ANALYSIS_SUMMARY_PROMPT = """
You are a senior software architect. Summarize the following code analysis results
in a clear, actionable format for a technical lead:

Analysis Results:
- Total Files: {total_files}
- Total Lines of Code: {total_lines}
- Languages: {languages}
- Quality Score: {quality_score}/100 (Grade: {quality_rating})
- Code Smells Found: {total_smells} (Critical: {critical_smells})
- Architectural Issues: {arch_issues} (High Severity: {high_sev_arch})
- Cyclic Dependencies: {cycles}
- Total Functions: {total_functions}
- Total Classes: {total_classes}
- Average Cyclomatic Complexity: {avg_complexity}

Provide:
1. Executive summary (2-3 sentences)
2. Key findings (3-5 bullet points)
3. Recommended immediate actions (3-5 items)
4. Long-term improvement roadmap
"""

REFACTORING_SUMMARY_PROMPT = """
You are a refactoring expert. Summarize the following refactoring plan
for a development team:

Refactoring Plan:
{refactoring_plan}

Provide:
1. Overview of the approach
2. Phase breakdown with effort estimates
3. Risk assessment summary
4. Key success metrics
5. Team recommendations
"""

DIFF_EXPLANATION_PROMPT = """
You are a technical documentation expert. Generate a clear, human-readable
explanation of the following code changes:

Changes: {changes}

Provide:
1. What changed and why
2. Impact on dependent code
3. Migration steps (if breaking)
4. Testing verification steps
5. Rollback procedure
"""

RISK_SUMMARY_PROMPT = """
You are a change risk analyst. Summarize the following risk assessment
for stakeholders:

Risk Assessment:
{risk_assessment}

Provide:
1. Overall risk rating
2. Key risk factors
3. Mitigation strategies
4. Go/no-go recommendation
"""
