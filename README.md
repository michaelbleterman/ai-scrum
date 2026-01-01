# AI Agent Sprint Runner

This repository contains the framework for running autonomous AI agent sprints.

## Structure

- `scripts/`: Core Python modules for the sprint runner.
    - `parallel_sprint_runner.py`: Main entry point for executing sprints.
    - `sprint_config.py`: Configuration management (loads from .env).
    - `sprint_tools.py`: Tools available to AI agents during execution.
    - `sprint_utils.py`: Utility functions for parsing sprint files.
- `tests/`: Test suite including E2E tests.
- `prompts/`: Agent prompt definitions and instructions.
- `project_tracking/`: **Generated during test execution** - Contains sprint logs, backlog, and artifacts.

## Setup

1.  **Environment Variables**:
    Create a `.env` file in `scripts/` with the following:
    ```env
    GOOGLE_API_KEY=your_api_key
    MODEL_NAME=gemini-3-flash-preview
    CONCURRENCY_LIMIT=3
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r scripts/requirements.txt
    ```

## Usage

To run the sprint runner:

```bash
python scripts/parallel_sprint_runner.py
```


## Testing

Run unit tests:

```bash
python -m unittest discover tests/
```

### End-to-End (E2E) Test Suite

Run the full lifecycle E2E test:

```bash
python tests/test_e2e_real.py
```

This test validates the complete sprint cycle:
1.  **Parallel Execution**: Multiple agents work on tasks concurrently.
2.  **QA Phase**: QA Agent verifies deliverables and detects defects.
3.  **Defect Resolution Loop**: Backend Agent fixes detected issues.
4.  **Re-verification**: QA Agent confirms fixes.
5.  **Demo & Retrospective**: Final reporting and documentation.

**Key Assertions**:
- All sprint tasks marked as complete (`[x]`)
- QA Report contains "PASSED" status
- Retrospective and backlog files generated
- Code defects resolved correctly
- Exit code 0 (CI-compatible)
