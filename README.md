# AI Agent Sprint Runner

This repository contains the framework for running autonomous AI agent sprints.

## Structure

- `scripts/`: Python scripts and modules.
    - `parallel_sprint_runner.py`: Main entry point.
    - `sprint_config.py`: Configuration management.
    - `sprint_tools.py`: Tools for agents.
    - `sprint_utils.py`: Utility functions.
- `tests/`: Unit tests.
- `prompts/`: Agent prompt definitions.
- `project_tracking/`: Sprint logs and backlog.

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

Run the full lifecycle E2E test (mocks user and agents):

```bash
python -m unittest tests/test_e2e_real.py
```

This test simulates:
1.  **Parallel Execution**: Agents create tasks.
2.  **QA Phase**: QA Agent detects a defect.
3.  **Defect Loop**: Backend Agent fixes the defect.
4.  **Verification**: QA Agent passes the fix.
5.  **Demo & Retro**: Orchestrator generates reports.
