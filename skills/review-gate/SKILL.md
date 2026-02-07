---
name: Review Gate
description: Pre-execution validation for tasks marked with [REVIEW] tag
---

# Review Gate Skill

This skill defines when and how to perform pre-execution review of tasks.

## When Review is Triggered

Review runs **ONLY** for tasks with the `[REVIEW]` tag:

```markdown
- [ ] @Backend: Implement OAuth2 authentication [REVIEW]
- [ ] @Frontend: Build admin dashboard [POINTS:8] [REVIEW]
```

Tasks **WITHOUT** `[REVIEW]` skip directly to execution:
```markdown
- [ ] @Backend: Fix typo in README [POINTS:1]
- [ ] @DevOps: Update version number
```

## PM Agent Guidelines for [REVIEW] Tag

Add `[REVIEW]` when:
- Task involves **external APIs** or third-party services
- Task modifies **authentication/authorization** logic
- Task has **complex dependencies** on other components
- Task is **8+ story points** (significant feature)
- Task involves **database schema changes**
- Task has **security implications**

Skip `[REVIEW]` for:
- Typo fixes, documentation updates
- Simple config changes
- Version bumps
- Straightforward CRUD operations
- Tasks under 3 story points with clear scope

## Reviewer Workflow

### Step 1: Analyze Task
Understand goal, requirements, and constraints.

### Step 2: Verify Context
```python
# Check documentation matches reality
search_codebase("relevant_function")
read_file("docs/architecture.md")
```

### Step 3: Identify Risks
- Ambiguous instructions
- Invalid design assumptions
- Breaking changes

### Step 4: Decision

| Decision | When | Action |
|----------|------|--------|
| APPROVE | Clear, safe task | Proceed |
| WARN | Valid but risky | Add context, proceed |
| BLOCK | Fundamentally broken | Mark `[!]` |

## Response Format

```
DECISION: [APPROVE | WARN | BLOCK]
REASON: Brief explanation
```

## Turn Budget
- Reviewer: Max 10 turns
- If can't decide in 10 turns, default to WARN and proceed
