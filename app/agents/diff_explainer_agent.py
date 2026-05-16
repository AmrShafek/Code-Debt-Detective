"""
Diff Explainer Agent
Generates human-friendly migration guides and actionable reports
Uses: DEEPSEEK via OpenRouter
"""

from typing import Optional
from crewai import Agent, Task, LLM


def create_diff_explainer(llm: Optional[LLM] = None):
    kwargs = dict(
        role="Technical Documentation Specialist",
        goal="Translate complex refactoring analysis into clear, actionable guides that non-specialists can follow",
        backstory="""You are an exceptional technical writer who bridges the gap between 
        architects and engineers. You excel at taking complex technical concepts and explaining 
        them in a way that's clear, concise, and actionable.
        You've written runbooks that prevented outages, migration guides that completed on schedule, 
        and breaking change notices that didn't cause panic.
        You always think about your audience: DevOps engineers, QA, product, leadership.""",
        verbose=True,
        allow_delegation=False,
        memory=False,
        max_iterations=5
    )
    if llm:
        kwargs["llm"] = llm
    return Agent(**kwargs)


def create_diff_explanation_task(agent, analysis_data, refactoring_plan, risk_assessment):
    return Task(
        description=f"""Create comprehensive, clear documentation for this refactoring:

ANALYSIS DATA:
{analysis_data}

REFACTORING PLAN:
{refactoring_plan}

RISK ASSESSMENT:
{risk_assessment}

Generate the following documents:

1. **Executive Summary** (1 page, for leadership)
   - Current state: debt score, key problems
   - Proposed solution: what we're doing
   - Business impact: reduced technical debt, faster features, less bugs
   - Timeline: 6-8 weeks
   - Investment: 120 engineer-days
   - Expected ROI: 30% faster feature delivery, 50% fewer production bugs

2. **Phase-by-Phase Migration Guide** (per phase)
   For EACH refactoring phase:
   
   **Phase N: [Name]**
   
   What's changing:
   - [Module X] → Extract to [new module]
   - [API Y] → Signature change
   - [DB] → Schema migration
   
   Why:
   - [Removes circular dependency X]
   - [Improves testability]
   - [Enables scaling]
   
   Step-by-step execution:
   1. Create feature branch from main
   2. Run these commands: [exact git/test commands]
   3. These tests must pass: [test names]
   4. Create PR with title: "Phase N: [description]"
   5. Deploy to staging
   6. Run this validation: [specific checks]
   7. Merge to main
   8. Deploy to production (canary 5% for 1 hour)
   9. Monitor these metrics: [what to watch]
   10. If issues: Run rollback script [link]
   
   Rollback procedure (if needed):
   - Command: [exact git command]
   - Time to rollback: 5 minutes
   - Data cleanup: [if any]

3. **Breaking Changes Documentation**
   Format as table:
   | Change | Old Behavior | New Behavior | Affected Teams | Migration |
   |--------|-------------|-------------|---|---|
   | UserService.get_user() signature | Returns {id, name} | Returns {id, name, email} | auth, profile | Add .email access |

4. **Integration Checkpoints**
   For services that integrate with changed modules:
   ```
   SERVICE: Payment Service
   BREAKING CHANGE: User ID format changes (string → UUID)
   
   WHAT TO DO:
   1. Add UUID validation in user_service_client.py
   2. Update test fixtures to use UUID format
   3. Deploy with feature flag "use_new_user_ids" OFF
   4. Once user_service deploys new API, switch flag ON
   5. Monitor error logs for stale code paths
   
   VALIDATION:
   - Run test_payment_with_uuid_user_id
   - Check logs for "invalid user_id" messages
   - Verify payments work end-to-end
   ```

5. **Testing Checklist**
   What to test at each phase:
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] E2E tests pass
   - [ ] Database migrations reversible
   - [ ] API contracts respected
   - [ ] Staging deployment successful
   - [ ] Performance not degraded
   - [ ] Monitoring alerts configured
   - [ ] Rollback procedure tested

6. **Communication Templates**
   
   **Slack announcement:**
   "Phase X refactoring ships tomorrow at 10 AM. Expected 0 customer impact. Watch #outages for updates."
   
   **Email to affected teams:**
   Subject: "Action required: UserService API changes (by Friday)"
   
   **PR description template:**
   ```
   ## Phase X: [Title]
   
   ### What changed
   [Clear list of changes]
   
   ### Why
   [Business/technical reason]
   
   ### Breaking changes
   - [List any]
   
   ### How to verify
   - [Test steps]
   
   ### Rollback
   [Simple command if issues]
   ```

7. **Runbook for Incidents**
   ```
   IF: Error "UserService returned unexpected format"
   THEN: 
   1. Check release notes for Phase X changes
   2. Your code expects {id, name}
   3. New API returns {id, name, email}
   4. Add field access: user.email
   5. Redeploy
   
   IF: "Cannot deserialize UUID"
   THEN:
   1. User IDs are now UUID, not int
   2. Update your database query
   3. Check data migration was successful
   4. Ask @devops to run validate_migrations.sh
   ```

Output everything as:
```json
{{
  "executive_summary": "...",
  "phases": [
    {{
      "name": "Phase 1: Extract utils",
      "guide": "...",
      "breaking_changes": [...],
      "testing_checklist": [...],
      "rollback_procedure": "..."
    }}
  ],
  "communication_templates": {{
    "slack": "...",
    "email": "...",
    "pr_template": "..."
  }},
  "integration_checkpoints": [
    {{
      "service": "...",
      "changes": [...],
      "steps": [...]
    }}
  ],
  "incident_runbook": "..."
}}
```

Write as if you're helping someone who has never done this before. Every step must be crystal clear.""",
        agent=agent,
        expected_output="Comprehensive migration guides, communication templates, testing checklists, and incident runbooks"
    )
