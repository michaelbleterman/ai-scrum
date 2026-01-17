
## Retrospective Action Items (From Sprint E2E Retrospective)

### Bug Fixes
- **Story:** Fix `add(a, b)` function in `project_tracking/dummy_math.py`.
    - **Priority:** High
    - **Acceptance Criteria:**
        - The `add(a, b)` function in `project_tracking/dummy_math.py` returns `a + b`.
        - A unit test is added to `dummy_math.py` to verify the correct addition.
    - **Role:** @Backend

### Process Improvements
- **Task:** Implement linter/pre-commit hook for sprint file formatting.
    - **Priority:** Medium
    - **Acceptance Criteria:**
        - A mechanism (linter/hook) is in place to validate sprint file formatting.
        - Sprint files consistently use `[POINTS:N]` and `[TURNS_ESTIMATED:N]` tags.
    - **Role:** @DevOps

- **Task:** Make `QA_REPORT.md` generation mandatory for every sprint.
    - **Priority:** Medium
    - **Acceptance Criteria:**
        - `QA_REPORT.md` is consistently generated at the end of each sprint.
        - `QA_REPORT.md` follows a predefined template.
    - **Role:** @QA
