# Global Agent Framework Index

This directory contains system prompts for the Scrum Team of specialized AI agents.

## Agent Roster

| Agent | File | Role |
|-------|------|------|
| Orchestrator | [agent_orchestrator.md](agent_orchestrator.md) | Workflow Manager & Coordinator |
| PM | [agent_product_management.md](agent_product_management.md) | Requirements & Validation |
| Frontend | [agent_frontend.md](agent_frontend.md) | UI/UX Development |
| Backend | [agent_backend.md](agent_backend.md) | API & Server Logic |
| DevOps | [agent_devops.md](agent_devops.md) | Infrastructure & CI/CD |
| QA | [agent_qa.md](agent_qa.md) | Testing & Validation |
| Security | [agent_security.md](agent_security.md) | Audit & Compliance |
| Reviewer | [agent_reviewer.md](agent_reviewer.md) | Pre-execution validation |

## Task States

| State | Symbol | Meaning |
|-------|--------|---------|
| Todo | `[ ]` | Not started |
| In Progress | `[/]` | Currently executing |
| Done | `[x]` | Completed and verified |
| Blocked | `[!]` | Requires `[BLOCKED: reason]` suffix |

## Skills Directory

Agents should load skills on-demand using `view_file`:

| Skill | Path | Description |
|-------|------|-------------|
| Environment Setup | `.agent/skills/environment-setup/SKILL.md` | QA/DevOps env verification |
| Defect Handling | `.agent/skills/defect-handling/SKILL.md` | Test-first bug fixing |
| Project Discovery | `.agent/skills/project-discovery/SKILL.md` | Tech stack detection |
| Test Execution | `.agent/skills/test-execution/SKILL.md` | Testing strategies |
| Review Gate | `.agent/skills/review-gate/SKILL.md` | `[REVIEW]` tag processing |

## Critical Protocols

### [REVIEW] Tag

Tasks with `[REVIEW]` tag go through Reviewer validation before execution:
```markdown
- [ ] @Backend: Implement OAuth2 [REVIEW]  # Will be reviewed
- [ ] @Backend: Fix typo [POINTS:1]         # Skips review
```

### Definition of Done

- Every task requires inline checklist (e.g., `- [ ] Tests pass`)
- PM sign-off required for story completion
- Evidence must be logged in task notes

### File Protection

- **NEVER** use `write_file` on existing sprint files
- **ALWAYS** use `update_sprint_task_status` for status changes
- **READ FIRST** before modifying any file

### Turn Budget

Call `request_turn_budget()` as FIRST action:
- Simple task: 20 turns
- Moderate: 40 turns
- Complex: 60 turns
- Story/Epic: 100 turns

### Messaging Protocol

1. **CHECK** `receive_messages(recipient='my_role')` at task start
2. **ACKNOWLEDGE** pending messages in reasoning
3. **REPLY** using `send_message` for updates

## Tool Guidelines

| Tool | Usage |
|------|-------|
| `search_codebase` | Find files before reading |
| `discover_project_context` | Detect tech stack |
| `run_command(..., background=True)` | Long-running processes |
| `cleanup_dev_servers` | Kill zombie processes |
| `find_process_by_port` | Debug port conflicts |
