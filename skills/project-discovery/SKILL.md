---
name: Project Discovery
description: Detect tech stack and project context before implementing changes
---

# Project Discovery Skill

This skill ensures you understand the existing codebase before making changes.

## When to Use
- Starting ANY new task
- Before creating new files
- Before choosing implementation approach

## Workflow

### Step 1: Discover Tech Stack

```python
context = discover_project_context(".")
# Returns: {"language": "Python", "frameworks": ["FastAPI"], ...}
```

### Step 2: Search for Existing Code

```python
# Find related implementations
search_codebase("user.*auth|registration")
search_codebase("class.*Controller|class.*Service")
```

### Step 3: Read Key Files

```python
# Understand patterns before coding
read_file("src/auth/userController.js")
read_file("requirements.txt")  # or package.json
```

### Step 4: Persist Context

```python
enrich_task_context(
    task_description="Add user registration endpoint",
    context_data={
        "tech_stack": "Node.js, Express.js",
        "related_files": "src/auth/userController.js",
        "patterns": "RESTful API, JWT authentication"
    }
)
```

## Critical Rules

> **NEVER** assume the tech stack without verification

> **NEVER** create parallel implementations in different languages

> **ALWAYS** match existing coding patterns and conventions

## Project Type Detection

| Indicator | Project Type |
|-----------|--------------|
| `package.json` + `node_modules` | Node.js |
| `requirements.txt` + `venv` | Python |
| `pom.xml` or `build.gradle` | Java |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

## Monorepo Awareness

If you see `apps/` or `packages/` directories:
- Place new code in existing structure
- NEVER create new root-level directories
- Follow existing naming conventions
