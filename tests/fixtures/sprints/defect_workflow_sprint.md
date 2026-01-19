# Sprint E2E - Defect Workflow
**Goal:** Verify full lifecycle with defect fix.
**Status**: Not Started
**Project Type**: Script/Library (No web server, no ports, pure Python functions)

## Context
This is a **simple Python script project** for testing basic functions:
- No web application
- No servers to run
- No ports to check
- Pure function validation only

### @Backend Tasks
- [ ] Create `project_tracking/dummy_math.py` with function `add(a, b)` that returns `a - b` (INTENTIONAL BUG) [POINTS:3].

### @Frontend Tasks
- [ ] Create `project_tracking/dummy_ui.txt` with text "Hello World" [POINTS:1].

## QA Instructions
**Project Type**: Script/Library
- Use inline test scripts (create test in `project_tracking/`)
- No need to start servers or check ports
- Validate by executing Python functions directly
- Expected artifacts: `dummy_math.py`, `dummy_ui.txt`
