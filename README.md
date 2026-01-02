# AI Agent Sprint Runner

A project-agnostic framework for running autonomous AI agent sprints using the Google Agent Development Kit (ADK).

## Overview

This framework enables you to run automated Scrum sprints with AI agents across **any project** on your machine. Each project maintains its own `project_tracking` folder for sprint management while sharing the centralized agent prompts and scripts.

## Structure

```
.agent/
├── scripts/              # Core Python modules
│   ├── parallel_sprint_runner.py  # Main sprint orchestrator
│   ├── sprint_config.py           # Dynamic configuration
│   ├── sprint_tools.py            # Agent tools & utilities
│   ├── sprint_utils.py            # Helper functions
│   └── .env                       # API keys & settings
├── prompts/              # Shared agent definitions
│   ├── agent_framework_index.md   # Framework overview
│   ├── agent_orchestrator.md      # Scrum Master agent
│   ├── agent_backend.md           # Backend Developer agent
│   ├── agent_frontend.md          # Frontend Developer agent
│   ├── agent_qa.md                # QA Engineer agent
│   └── ...
├── workflows/            # Reusable workflows
│   └── run-sprint.md              # /run-sprint command
├── tests/                # Test suite
└── project_tracking/     # Test fixtures only (empty in production)
```

## Project-Agnostic Design

The sprint runner **automatically detects your project directory** and uses its local `project_tracking` folder:

```
Your Project (e.g., C:\git\MyProject)
├── project_tracking/
│   ├── backlog.md
│   ├── SPRINT_1.md
│   ├── SPRINT_2.md
│   └── ...
├── src/
├── tests/
└── .env             # Contains GOOGLE_API_KEY
```

**Key Features**:
- ✅ Run sprints from any project directory
- ✅ Each project has isolated tracking
- ✅ Shared agent prompts across all projects
- ✅ Automatic project root detection

## Setup

### 1. Install Dependencies

```powershell
pip install -r scripts/requirements.txt
```

### 2. Configure API Key

Create a `.env` file in your **project directory** (or in `scripts/`):

```env
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-3-flash-preview
CONCURRENCY_LIMIT=3
```

### 3. Initialize Project Tracking

In your project directory, create:

```powershell
mkdir project_tracking
```

Add initial files:
- `backlog.md` - Product backlog
- `SPRINT_1.md` - First sprint plan

## Usage

### Option 1: Using the Workflow (Recommended)

From any project directory with a `project_tracking` folder:

```powershell
/run-sprint
```

This executes the sprint runner with your current directory as the project root.

### Option 2: Direct Script Execution

```powershell
# From your project directory
C:\Users\Michael\.gemini\.agent\scripts\.venv\Scripts\python.exe `
  C:\Users\Michael\.gemini\.agent\scripts\parallel_sprint_runner.py `
  --project-root "$PWD"

# Or specify a different project
python scripts/parallel_sprint_runner.py --project-root "C:\git\MyProject"
```

### Option 3: Default to Current Directory

```powershell
cd C:\git\MyProject
python C:\Users\Michael\.gemini\.agent\scripts\parallel_sprint_runner.py
# Automatically uses C:\git\MyProject\project_tracking
```

## How It Works

1. **Sprint Detection**: Finds the latest `SPRINT_*.md` file in `project_tracking/`
2. **Parallel Execution**: Spawns specialized agents (@Backend, @Frontend, @QA, etc.) to work on tasks concurrently
3. **QA Verification**: Validates completed work and creates defect tickets if needed
4. **Defect Resolution Loop**: Re-runs execution phase to fix detected issues
5. **Demo & Retrospective**: Generates reports and updates backlog

## Testing

### Run Unit Tests

```powershell
python -m unittest discover tests/
```

### Run E2E Test

```powershell
python tests/test_e2e_real.py
```

**What the E2E test validates**:
1. ✅ Parallel agent execution
2. ✅ QA defect detection
3. ✅ Automated defect resolution
4. ✅ Report generation (QA, Demo, Retrospective)
5. ✅ Backlog updates
6. ✅ Exit code 0 (CI-compatible)

## CLI Reference

```powershell
python scripts/parallel_sprint_runner.py [OPTIONS]

Options:
  --project-root PATH    Project root directory (defaults to current working directory)
  -h, --help            Show help message
```

## Agent Roles

The framework includes specialized agents:

- **Orchestrator** (Scrum Master) - Coordinates workflow and task dependencies
- **Product Manager** - Manages requirements and acceptance criteria
- **Backend Developer** - Implements APIs and server logic
- **Frontend Developer** - Builds UI/UX components
- **DevOps Engineer** - Handles infrastructure and CI/CD
- **QA Engineer** - Writes and runs automated tests
- **Security Engineer** - Performs security audits

## Examples

### Running a Sprint for Your Project

```powershell
cd C:\git\MyProject
# Ensure project_tracking/ exists with backlog.md and SPRINT_1.md
/run-sprint
```

### Running from a Different Directory

```powershell
cd C:\git\SomeOtherProject
python C:\Users\Michael\.gemini\.agent\scripts\parallel_sprint_runner.py `
  --project-root "C:\git\MyProject"
```

## Configuration

### Environment Variables

Create a `.env` file in your **project directory** (or in `scripts/`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google Gemini API key |
| `MODEL_NAME` | `gemini-2.5-flash` | Default LLM model (fallback) |
| `CONCURRENCY_LIMIT` | `3` | Max parallel agents |
| `PROMPT_BASE_DIR` | `.agent/prompts` | Agent prompt directory (shared) |

### Agent-Specific Models (Optional)

The framework automatically selects optimal models for each agent type based on their complexity. You can override these defaults:

| Variable | Default Model | Agent Type |
|----------|---------------|------------|
| `MODEL_ORCHESTRATOR` | `gemini-2.5-pro` | Orchestrator (workflow coordination) |
| `MODEL_QA` | `gemini-2.5-pro` | QA Engineer (comprehensive testing) |
| `MODEL_BACKEND` | `gemini-2.5-flash` | Backend Developer |
| `MODEL_FRONTEND` | `gemini-2.5-flash` | Frontend Developer |
| `MODEL_DEVOPS` | `gemini-2.5-flash` | DevOps Engineer |
| `MODEL_SECURITY` | `gemini-2.5-flash` | Security Engineer |
| `MODEL_PM` | `gemini-2.5-flash` | Product Manager |

**Example `.env`:**
```env
GOOGLE_API_KEY=your_google_api_key_here
MODEL_NAME=gemini-2.5-flash

# Optional: Override specific agent models
MODEL_ORCHESTRATOR=gemini-3-pro
MODEL_QA=gemini-2.5-flash
```

See [`MODEL_SELECTION.md`](MODEL_SELECTION.md) for detailed model capabilities, pricing, and optimization strategies.

**Note**: `SPRINT_DIR` is now dynamically set based on `--project-root` or current directory.

## Troubleshooting

**Issue**: "No sprint files found"
- Ensure `project_tracking/` exists in your project
- Add at least one `SPRINT_*.md` file

**Issue**: API rate limits
- Reduce `CONCURRENCY_LIMIT` in `.env`
- The framework includes automatic retry logic

**Issue**: Agents can't find files
- All file paths in sprint files should be relative to project root
- Example: `project_tracking/backlog.md`, `src/main.py`

## Contributing

See the [prompts/](prompts/) directory to customize agent behaviors or add new specialized agents.
