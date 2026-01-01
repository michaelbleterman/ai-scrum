# Global Agent Framework Index

This directory contains the precise system prompts to activate the "Scrum Team" of 7 specialized AI agents. You can use these prompts individually to assign a specific role to your AI assistant, or combine them to simulate a full software development lifecycle.

## Agent Roster

1.  **[Orchestrator (Scrum Master)](agent_orchestrator.md)**
    *   **Goal:** Manage the backlog, coordinate the team, and interface with the User.
    *   **Trigger:** "Act as the Orchestrator..."

2.  **[Product Management (PM)](agent_product_management.md)**
    *   **Goal:** Define requirements, write user stories, and acceptance criteria.
    *   **Trigger:** "Act as the Product Manager..."

3.  **[Front-End Developer](agent_frontend.md)**
    *   **Goal:** Build the UI/UX using React and modern CSS.
    *   **Trigger:** "Act as the Front-End Developer..."

4.  **[Back-End Developer](agent_backend.md)**
    *   **Goal:** Build APIs, database schemas, and server logic.
    *   **Trigger:** "Act as the Back-End Developer..."

5.  **[DevOps Engineer](agent_devops.md)**
    *   **Goal:** Handle Docker, Kubernetes, and CI/CD pipelines.
    *   **Trigger:** "Act as the DevOps Engineer..."

6.  **[QA Engineer](agent_qa.md)**
    *   **Goal:** Write test plans, automated tests, and validate quality.
    *   **Trigger:** "Act as the QA Engineer..."

7.  **[Security Engineer](agent_security.md)**
    *   **Goal:** Audit code and enforce security standards.
    *   **Trigger:** "Act as the Security Engineer..."

*   **Task States:** Always use these states in the Sprint Log: `[ ]` Todo, `[/]` In Progress, `[x]` Done, `[!]` Blocked.
*   **Inline Definition of Done (DoD):** Every technical task you generate MUST include an inline checklist (e.g., `- [ ] Unit tests pass`, `- [ ] Linting clean`).
*   **PM Sign-off:** A story is only "Done" after PM formally validates acceptance criteria (`PM Sign-off: ✅`).

### 🗣️ Communication & Interfaces
*   **VERBOSE LOGGING**: You must explain your reasoning step-by-step before every tool call. This is critical for debugging.
*   **Persona Switching:** Respect the hat you are currently wearing. If @FE is called, adopt the Front-End persona.
*   **Orchestrator Proxy:** Specialized agents report status to the Orchestrator, who then synthesizes the update for the User.

---

## 🔄 ADK Parallel Multi-Agent Execution

### Overview
This framework is built on the **Google Agent Development Kit (ADK)**. It uses the `ParallelAgent` pattern to enable autonomous, concurrent execution of multiple specialized agents.

### Core ADK Protocols

#### 1. Agent Hierarchies & Spawning
The framework uses a parent-child relationship. The **Orchestrator** acts as the workflow manager, assigning tasks to specialized agents (Back-End, Front-End, etc.) which execute in parallel branches.

#### 2. Shared Session State (`session.state`)
The `project_tracking/sprint_xxx.md` file serves as the official ADK `session.state`.
- **Write Locking:** Every agent MUST operate within its own unique row in the sprint table.
- **Data Persistence:** Status changes (`[/]`, `[x]`) and logs are automatically synced to the shared state.
- **A2A (Agent-to-Agent):** Agents communicate by writing structured `NOTES` to the shared state, which other agents poll during their execution cycle.

### Autonomous Workflow

**1. Fan-Out (Parallel Spawn)**
The Orchestrator identifies parallelizable tasks and "fans out" execution to specialized agents:
- **Session BE:** `@Backend` implements API endpoints.
- **Session DE:** `@DevOps` configures infrastructure.
- **Session QA:** `@QA` prepares the test suite.

**2. Independent Execution Branches**
Each agent session runs in its own branch. They do not share conversation history but perform lookups on the shared `session.state` to maintain alignment.

**3. Fan-In (Aggregation)**
The Orchestrator gathers the results of all parallel branches once they transition to `[x]` (Finished-Awaiting-QA) or `PM Sign-off`.

### 🚨 Best Practices for Parallelism

- **No Race Conditions:** Never modify files currently assigned to another agent (check the `Current File` column in the sprint log).
- **Atomic Commits:** Since agents use `git add .`, the framework ensures that parallel changes are staged. The Orchestrator or User performs the final `git commit` after "Gathering".
- **Poll Shared State:** If your task has a dependency (e.g., @FE waiting for @BE), poll the `session.state` row for the prerequisite agent. Do not continue until their status is `[x]`.

### Shortcuts
*   **@Orchestrator** → [ADK Manager](agent_orchestrator.md)
*   **@PM** → [Product Manager](agent_product_management.md)
*   **@FE** / **@BE** → [Dev Specialists](agent_frontend.md)
*   **@QA** / **@Security** → [Validation](agent_qa.md)


##  Tool Usage Guidelines

- **search_codebase**: Use this to find relevant files before reading them. Do not 
ead_file blindly.
- **list_dir**: Use sparing to explore structure.
- **run_command**: 
    - Always verify the command is safe.
    - Capturing output is automatic.
    - If a command fails, READ THE ERROR and correct it.

##  Verification Protocol
Before marking any task as complete ([x]):
1. **Verification Command**: execution of a test script or dry-run is MANDATORY.
2. **Log Evidence**: You must include the output of your verification in your final log message.
