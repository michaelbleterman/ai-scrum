# Workflow: Cross-Project Autonomous Agile
# Context: ./project_tracking/

## Phase 1: Planning (Trigger: /plan)
- PM Agent scans `project_tracking/backlog.md`.
- PM creates `project_tracking/sprint_{{ID}}.md`.
- **Parallel Sync:** All agents (6) read the file and add technical sub-tasks.
- **Wait:** User approval of the `sprint_{{ID}}.md` artifact.

## Phase 2: Execution (Sequential or Parallel)

**Sequential Mode (Default - Fully Automated):**
```
loop while (sprint_status != "Verified"):
  - Orchestrator reads sprint_{{ID}}.md and finds next `[ ]` task
  - Orchestrator reads agent definition file for assigned role
  - Orchestrator adopts agent persona and executes task
  - Updates sprint file: `[ ]` → `[/]` → `[x]` with logs
  - Returns to Orchestrator persona
  - Proceeds to next task
```

**Parallel Mode (Fully Automated - ADK Driven):**
```
- Orchestrator triggers `python .agent/scripts/parallel_sprint_runner.py`
- Runner parses `project_tracking/sprint_{{ID}}.md` for task table
- Runner spawns official `google.adk.agents.ParallelAgent`
- Specialized agents (@Backend, @Frontend, etc.) execute concurrently
- Agents sync status and logs back to the sprint markdown file
- Orchestrator gathers results and proceeds to next dependency wave
```

## Phase 3: Closure
- **Demo:** Orchestrator generates `DEMO_WALKTHROUGH.md` in `project_tracking/`.
- **Retro:** Agents append "Lessons Learned" to `backlog.md`.