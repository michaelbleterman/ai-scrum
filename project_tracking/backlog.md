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
- **[ ] Story: Improve clarity in defect demonstration scenarios**
    - *Description:* Enhance task definitions for intentional defects to explicitly state the initial incorrect code.
    - *Acceptance Criteria:*
        - Task definitions for intentional defects explicitly state the initial incorrect code.
        - QA reports clearly distinguish between a true defect fix and verification of pre-existing correct code.
        - **(Added from Retrospective):** Include a pre-implementation clarification step and explicit bug confirmation in DoD for intentional bug tasks.

## 🟡 Medium Priority
- **[ ] Story: CI/CD Pipeline Setup**
    - *Description:* Add GitHub Actions for automated testing.
- **[ ] Story: Dockerization**
    - *Description:* Create Dockerfiles for both FE and BE.
- **[ ] Process Improvement: Continuous Process Improvement and Refinement**
    - *Description:* Regularly review and refine development and QA processes based on sprint retrospectives to maximize efficiency and quality.
    - *Acceptance Criteria:*
        - Retrospective action items are consistently implemented in subsequent sprints.
        - Measurable improvements in sprint velocity or defect reduction over time.
- **[ ] Feature Exploration: Explore Complex Features for Future Demos**
    - *Description:* Research and propose more advanced features and integrations to showcase in upcoming sprint demos, building on the positive user feedback.
    - *Acceptance Criteria:*
        - A list of 2-3 complex feature ideas is generated for review.
        - Each feature idea includes a high-level description and potential benefits for demo purposes.
- **[ ] Process Improvement: Continuously monitor and refine turn estimations**
    - *Description:* Regularly review actual vs. estimated turn usage to improve estimation accuracy for future sprints.
    - *Acceptance Criteria:*
        - Turn estimation accuracy shows a positive trend over subsequent sprints.
        - A baseline turns-per-story-point metric is consistently tracked and refined.
- **[ ] Process Improvement: Explore more complex features for future demonstration sprints**
    - *Description:* Based on positive demo feedback, identify and plan for the inclusion of more sophisticated functionalities in upcoming E2E demonstration sprints.
    - *Acceptance Criteria:*
        - A proposal for 2-3 complex feature ideas is drafted for review.
        - These features effectively showcase a broader range of the development lifecycle.
- **[ ] Process Improvement: Review and update turn estimation guidelines**
    - *Description:* Review and update the guidelines for estimating turn budgets, especially for smaller, well-defined tasks, to improve accuracy based on recent sprint's overestimation.
    - *Acceptance Criteria:*
        - New turn estimation guidelines are documented and communicated.
        - A noticeable improvement in turn estimation accuracy is observed in subsequent sprints.
- **[ ] Process Improvement: Refine Defect Workflow for Intentional Bugs**
    - *Description:* Implement a clearer protocol for scenarios involving intentional bugs for process verification. Ensure QA confirms the bug *before* a fix is implemented by development.
    - *Acceptance Criteria:*
        - New tasks for intentional bugs include a dedicated "verify bug" step for QA.
        - Development only proceeds with bug fixes after formal QA confirmation.
    - *Priority:* Medium
- **[ ] Process Improvement: Enhance Turn Estimation Accuracy**
    - *Description:* Refine turn estimation guidelines and practices to reduce overestimation for simple tasks and establish a more reliable turns-per-story-point baseline.
    - *Acceptance Criteria:*
        - Updated turn estimation guidelines are documented.
        - A reduction in the variance between estimated and actual turns is observed in subsequent sprints.
        - The turns-per-story-point metric is consistently tracked and used for future planning.
    - *Priority:* Medium

## ⚪ Low Priority
- **[ ] Story: User Authentication**
- **[ ] Story: Database Integration (PostgreSQL)**

---
*Last Updated by ProductManager Agent*