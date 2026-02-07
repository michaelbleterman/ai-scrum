---
name: Environment Setup
description: Verify and prepare test environments for QA and DevOps tasks
---

# Environment Setup Skill

This skill provides procedures for verifying and preparing test environments.

## When to Use
Load this skill when:
- Starting QA verification tasks
- Setting up test infrastructure
- Debugging environment issues

## Step 1: Identify Project Type

```python
# Use discover_project_context() or check for indicators
project_type = "script"  # Default

# Web app indicators
if any file in ["app.py", "server.js", "main.py", "index.js"]:
    project_type = "web_app"
```

## Step 2: For Script/Library Projects

**Simple validation - NO servers needed:**

1. Verify files exist in `project_tracking/`
2. Syntax check: `python -m py_compile file.py`
3. Mark "Environment Ready" - **max 5 turns**

## Step 3: For Web Application Projects

1. **Check if services running:**
   ```bash
   curl http://localhost:PORT/health
   # or check with find_process_by_port(PORT)
   ```

2. **Start if needed:**
   ```python
   run_command("npm run dev", background=True)
   # Wait and verify port is listening
   ```

3. **Cleanup zombie processes first:**
   ```python
   cleanup_dev_servers()  # Kills stale vite/node/python processes
   ```

## Step 4: Failure Protocol

- If environment cannot be ready in **5 turns** → Mark BLOCKED
- Do NOT spend 20+ turns debugging infrastructure
- Document specific blocker: `"Port 5173 occupied by PID 1234"`

## Turn Budget
- Script projects: Max 5 turns
- Web app projects: Max 15 turns
- If blocked after limit, STOP and report
