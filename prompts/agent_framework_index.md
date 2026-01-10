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

*   **Task States:** Always use these states in the Sprint Log:
    - `[ ]` Todo
    - `[/]` In Progress
    - `[x]` Done
    - `[!]` Blocked - **MUST** include blocker reason at end of description in format: `[BLOCKED: reason]`
      - Example: `- [!] @Backend: API integration [BLOCKED: Missing OAuth credentials]`
      - Example: `- [!] @QA: Test execution [BLOCKED: Test data not available]`
*   **Inline Definition of Done (DoD):** Every technical task you generate MUST include an inline checklist (e.g., `- [ ] Unit tests pass`, `- [ ] Linting clean`).
*   **PM Sign-off:** A story is only "Done" after PM formally validates acceptance criteria (`PM Sign-off: ✅`).

### 🗣️ Communication & Interfaces
*   **VERBOSE LOGGING**: You must explain your reasoning step-by-step before every tool call. This is critical for debugging.
*   **Persona Switching:** Respect the hat you are currently wearing. If @FE is called, adopt the Front-End persona.
*   **Orchestrator Proxy:** Specialized agents report status to the Orchestrator, who then synthesizes the update for the User.

---

## 🔍 Project Context Discovery Protocol

**MANDATORY FIRST STEPS** for ALL agents before starting ANY task:

### 1. Discover Tech Stack
Call `discover_project_context()` to identify:
- Primary programming language(s) in use
- Frameworks and libraries
- Package managers (npm, pip, etc.)
- Existing code patterns and structure

### 2. Search Before Create
Use `search_codebase()` to find:
- Existing implementations you should extend
- Similar features already built
- Code patterns and conventions to follow

### 3. Read and Understand
Use `read_file()` on relevant files to:
- Understand the existing architecture
- Match coding style and patterns
- Identify integration points

### 4. Enrich Task with Context
After discovering context, **persist it** to the sprint file:

Call `enrich_task_context()` with discovered information:
- Tech stack detected
- Related files found
- Patterns identified
- Dependencies discovered

This ensures context survives sprint interruptions and helps with resume.

**Example**:
```python
enrich_task_context(
    task_description="Add user registration endpoint",
    context_data={
        "tech_stack": "Node.js, Express.js",
        "related_files": "src/auth/userController.js, src/models/User.js",
        "patterns": "RESTful API, JWT authentication",
        "dependencies": "express-validator, bcrypt"
    }
)
```

### Critical Rules

> [!CAUTION]
> **Tech Stack Compliance**
> 
> You MUST use the same tech stack as the existing project. Creating new implementations in a different language/framework than what exists is a CRITICAL FAILURE.

**Example Workflow:**
```
1. discover_project_context(".")  # Returns: Node.js, Express, React
2. search_codebase("user.*auth|registration")  # Find existing auth code
3. read_file("src/auth/userController.js")  # Understand patterns
4. Extend existing Node.js/Express code (NOT Python/Flask!)
5. enrich_task_context(...) # Persist discoveries for resume
```

**Never:**
- Assume the tech stack without verification
- Create parallel implementations in different languages
- Ignore existing code that should be extended

---

## 🔄 ADK Parallel Multi-Agent Execution

### Overview
This framework is built on the **Google Agent Development Kit (ADK)**. It uses the `ParallelAgent` pattern to enable autonomous, concurrent execution of multiple specialized agents.

### Core ADK Protocols

#### 1. Agent Hierarchies & Spawning
The framework uses a parent-child relationship. The **Orchestrator** acts as the workflow manager, assigning tasks to specialized agents (Back-End, Front-End, etc.) which execute in parallel branches.

#### 2. Shared Session State (`session.state`)
The `project_tracking/sprint_xxx.md` file serves as the official ADK `session.state`.
- **Project-Relative Paths:** All file paths (e.g., `project_tracking/backlog.md`) are relative to the project root directory where the sprint runner executes.
- **Write Locking:** Every agent MUST operate within its own unique row in the sprint table.
- **Data Persistence:** Status changes (`[/]`, `[x]`) and logs are automatically synced to the shared state.
- **A2A (Agent-to-Agent):** Agents communicate by writing structured `NOTES` to the shared state, which other agents poll during their execution cycle.

### 2a. Critical File Protection Rules ⚠️
- **NEVER** use `write_file` on existing sprint files (SPRINT_*.md) - it will error by default
- **ALWAYS** use `update_sprint_task_status` to modify sprint task statuses
- **READ FIRST**: Always use `read_file` before modifying any file to understand current state
- **BACKUP**: `write_file` with `overwrite=True` automatically creates timestamped backups
- **CHECK EXISTS**: Use `read_file` to verify if a file exists before attempting to create it

## 🛡️ Smart Context Discovery & Safety Protocol

**MANDATORY: You must determine if this is an Existing or New Project before acting.**

### Phase 1: Context Detection
Before running ANY tools, ask: "Am I in a new or existing project?"
1.  **Check for Indicators:** `package.json`, `.git`, `requirements.txt`, `pom.xml`, etc.
2.  **IF EXISTING PROJECT FOUND:**
    *   **Rule:** You MUST align with the established structure.
    *   **Monorepos:** If you see `apps/` or `packages/`, you MUST place new code there. NEVER create a new root-level project directory.
    *   **Tech Stack:** You MUST use the discovered stack (e.g., mismatching Mongoose vs TypeORM is a fatal error).
3.  **IF NEW PROJECT (EMPTY RESOURCE):**
    *   **Rule:** You are free to scaffold, but PREFER standard monorepo patterns (e.g., `apps/[project-name]`) for future scalability.

### Phase 2: Directory Awareness (Universal Rule)
**CRITICAL:** Before running any initialization command (e.g., `npm init`, `create-react-app`, `mkdir`, `dotnet new`):
1.  **Verify CWD:** Run `pwd` or `list_dir` to confirm exactly where you are.
2.  **Target Correctly:**
    *   **WRONG:** Running `create-react-app my-app` inside `C:\path\to\project` -> creates `C:\path\to\project\my-app`.
    *   **RIGHT:** `cd apps/` -> `create-react-app my-app` -> creates `C:\path\to\project\apps\my-app`.


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


## ⚖️ Turn Budget Protocol

**MANDATORY:** Before starting any turn-intensive task (coding, testing, large research), you must request a turn budget.

1. **Calculate Needs:** Estimate the complexity of the task.
   - Simple (e.g., config change): 20 turns
   - Moderate (e.g., new file): 40 turns
   - Complex (e.g., full feature): 60 turns
   - Story/Epic: 100 turns

2. **Request Budget:** Call `request_turn_budget(task_description="...", estimated_turns=N, justification="...")`.
   - **Do this in your very first turn** after picking up the task.
   - The runner will approve and dynamically update your limit.

3. **Monitor Usage:** Work efficiently. If you are running out of turns, simplify your approach or mark as BLOCKED.

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
