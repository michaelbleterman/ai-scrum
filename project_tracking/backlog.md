# Product Backlog

---

## User Stories & Features

### High Priority
- **STORY:** As a user, I expect the `add` function to perform addition correctly.
  - **Task:** Fix the `add()` function in `dummy_math.py` to return `a + b`.
  - **Acceptance Criteria:**
    - `add(2, 3)` must return `5`.
    - The fix must be accompanied by a new or updated unit test that fails before the fix and passes after.
  - **Priority:** High
  - **Role:** @Backend

### Medium Priority
- **STORY:** As a user, I want to see a more descriptive UI message.
  - **Task:** Enhance the `dummy_ui.txt` file.
  - **Acceptance Criteria:**
    - The `dummy_ui.txt` is updated with a more descriptive message acknowledging the successful demo.
  - **Priority:** Medium
  - **Role:** @Frontend

---

## Process Improvements & Technical Debt

### High Priority
- **TASK:** The `analyze_turn_metrics()` tool is not parsing sprint files correctly.
  - **Story:** Fix the turn metric collection and parsing process.
  - **Acceptance Criteria:**
    - The `analyze_turn_metrics()` tool must return accurate data for completed sprints.
    - A clear, consistent format for logging Story Points (e.g., `[POINTS: 3]`) and Turns (e.g., `[TURNS_ESTIMATED:20|TURNS_USED:15]`) is documented and used by all agents.
    - The Sprint Report generation process automatically includes an accurate turn budget analysis.
  - **Priority:** High
  - **Role:** @DevOps / @Orchestrator

### Medium Priority
- **TASK:** Our Definition of Done (DoD) for bug fixes is not explicit enough.
  - **Story:** Mandate developer-led verification for all bug fixes.
  - **Acceptance Criteria:**
    - The official Definition of Done (DoD) is updated to state that a bug fix task is not complete until a corresponding unit test is passing.
    - Developers must submit proof of the passing test (e.g., a log) when marking a task as `[x]`.
  - **Priority:** Medium
  - **Role:** @Orchestrator

- **TASK:** Sprints involving intentional defects can be confusing.
  - **Story:** Create separate tasks for intentional defect introduction and fixing.
  - **Acceptance Criteria:**
    - When a sprint involves an intentional defect, the sprint plan will include two distinct tasks: one for creating the defect and one for fixing it.
  - **Priority:** Medium
  - **Role:** @PM

### Low Priority
- **TASK:** Our turn estimations are not consistently accurate.
  - **Story:** Review and refine turn estimation guidelines.
  - **Acceptance Criteria:**
    - An analysis of "Estimated vs. Actual Turns" is conducted for at least the last 3 sprints.
    - Updated guidelines for estimating tasks are documented.
    - A baseline "turns per story point" is established or refined.
  - **Priority:** Low
  - **Role:** @PM / @Orchestrator

---

## Feedback
- **NOTE:** The user provided positive feedback: "Great demo!" Thank the team for their excellent work. This indicates strong performance on the previous sprint's deliverables.

*This backlog was cleaned and consolidated during the retrospective following the E2E Defect Workflow sprint.*
