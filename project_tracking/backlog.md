# Product Backlog

This backlog tracks future enhancements and features for the Project.

## 🟢 High Priority (Next Sprint)
- **[ ] Story: Implement Real API Structure**
    - *Description:* Replace `dummy_api.py` with a Flask or FastAPI skeleton.
    - *Acceptance Criteria:*
        - Endpoint `/health` returns JSON `{"status": "healthy"}`.
        - Unit tests for the endpoint.
- **[ ] Story: Basic React Frontend**
    - *Description:* Initialize a React application to replace the `dummy_ui.txt`.
    - *Acceptance Criteria:*
        - `App.js` displays "Project Dashboard".
        - Fetches health status from API.
- **[ ] Story: Fix mathematical error in `add` function**
    - *Description:* Correct the `add` function in `project_tracking/dummy_math.py` to return the sum of two numbers instead of their difference.
    - *Acceptance Criteria:*
        - `add(5, 3)` returns `8`.
        - Unit tests confirm correct addition.
- **[ ] Story: Enhance Frontend to display `add` function result**
    - *Description:* Modify the React frontend to call the backend `add` function and display its result.
    - *Acceptance Criteria:*
        - Frontend displays the result of `add(x, y)` from the backend.
        - User can input two numbers and see their sum.
- **[ ] Story: Implement Mandatory QA Report Generation**
    - *Description:* Ensure a `QA_REPORT.md` is generated and completed for every sprint.
    - *Acceptance Criteria:*
        - `QA_REPORT.md` exists and contains metrics for each completed sprint.
- **[ ] Story: Improve Sprint Task Status Tracking**
    - *Description:* All agents must consistently and accurately update task statuses in the sprint file, including detailed blocker reasons.
    - *Acceptance Criteria:*
        - Sprint file tasks are always up-to-date with correct `[ ]`, `[/]`, `[x]`, or `[!]` statuses and blocker reasons.
- **[ ] Story: Enforce Turn Budget Protocol**
    - *Description:* Ensure all agents request and record turn budgets for their tasks.
    - *Acceptance Criteria:*
        - All tasks have an `estimated_turns` and `turns_used` recorded.

## 🟡 Medium Priority
- **[ ] Story: CI/CD Pipeline Setup**
    - *Description:* Add GitHub Actions for automated testing.
- **[ ] Story: Dockerization**
    - *Description:* Create Dockerfiles for both FE and BE.
- **[ ] Task: Review and Refine "Full Lifecycle" Sprint Definition**
    - *Description:* Update sprint definitions to explicitly include defect resolution, comprehensive QA, and formal reporting for "full lifecycle" sprints.
    - *Description:* Improve the `analyze_turn_metrics` tool to ensure automated and accurate extraction of turn data from sprint files.
    - *Acceptance Criteria:*
        - The tool successfully parses turn estimation and usage from sprint files.
        - Provides accurate statistics on turn usage deviations.
- **[ ] Task: Refine Turn Estimation Process**
    - *Description:* Investigate the reasons for overestimation of turns in the previous sprint and refine the turn estimation guidelines for future sprints.
    - *Acceptance Criteria:*
        - Updated guidance for agents on estimating turns, leading to more accurate estimates.
        - Reduced deviation between estimated and actual turns in subsequent sprints.

## ⚪ Low Priority
- **[ ] Story: User Authentication**
- **[ ] Story: Database Integration (PostgreSQL)**

### New Items from Sprint Retrospective

#### User Stories
- [ ] As a User, I want to see a functional demo of the `add` function so that I can verify the intended defect and the fix. (Priority: High) [PM Sign-off: [ ]] 

#### Follow-up Tasks
- [ ] Investigate why `project_tracking/dummy_math.py` was marked `[x]` Done but was not created. (Priority: High)
- [ ] Implement a "Pre-QA Check" to verify the existence of all critical files and dependencies before initiating the formal QA process. (Priority: Medium)
- [ ] Introduce a mandatory artifact verification step for agents to confirm successful file creation/modification before marking a task as `[x]` Done. (Priority: Medium)

---
*Last Updated by ProductManager Agent*
