# Sprint Test Fixtures

This directory contains reusable sprint test scenarios for different testing needs.

## Available Fixtures

### `minimal_sprint.md`
Single task, basic validation. Use for quick smoke tests.

### `defect_workflow_sprint.md`  
Contains intentional bug to test QA defect detection and fixing workflow.

### `blocked_task_sprint.md`
Pre-blocked task to test unblock workflow and retry logic.

### `multi_role_sprint.md`
Multiple roles working in parallel. Tests concurrency and role assignment.

### `epic_sprint.md`
Epic/Story structure to test hierarchical task parsing.

## Usage

```python
import shutil

# Copy fixture to test location
fixture_path = "tests/fixtures/sprints/minimal_sprint.md"
test_sprint = "project_tracking/SPRINT_TEST.md"
shutil.copy(fixture_path, test_sprint)
```
