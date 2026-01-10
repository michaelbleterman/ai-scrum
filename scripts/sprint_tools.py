import os
import re
import subprocess
import logging
import functools
from google.adk.tools import FunctionTool
from sprint_utils import detect_latest_sprint_file

# --- Tool Logging Decorator ---
def log_tool_usage(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("SprintRunner")
        try:
            logger.info(f"[Tool] Invoking {func.__name__}")
            result = func(*args, **kwargs)
            # Truncate result for logging if too long
            str_res = str(result)
            str_res = str_res.encode('ascii', 'replace').decode('ascii')
            log_res = str_res if len(str_res) < 500 else str_res[:500] + "...(truncated)"
            logger.info(f"[Tool] {func.__name__} returned: {log_res}")
            for h in logger.handlers: h.flush()
            return result
        except Exception as e:
            logger.error(f"[Tool] {func.__name__} FAILED: {e}")
            raise e
    return wrapper

# Async wrapper for async tools
def log_async_tool_usage(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger("SprintRunner")
        try:
            logger.info(f"[Tool] Invoking {func.__name__}")
            result = await func(*args, **kwargs)
            # Sanitize result for logging
            str_res = str(result)
            str_res = str_res.encode('ascii', 'replace').decode('ascii')
            log_res = str_res if len(str_res) < 500 else str_res[:500] + "...(truncated)"
            logger.info(f"[Tool] {func.__name__} returned: {log_res}")
            for h in logger.handlers: h.flush()
            return result
        except Exception as e:
            logger.error(f"[Tool] {func.__name__} FAILED: {e}")
            raise e
    return wrapper

@log_tool_usage
def list_dir(path: str = "."):
    """Lists files and directories in the specified path."""
    try:
        return os.listdir(path)
    except Exception as e:
        return f"Error: {e}"

@log_tool_usage
def read_file(path: str):
    """Reads the content of a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

@log_tool_usage
def write_file(path: str, content: str, overwrite: bool = False):
    """
    Writes content to a file.
    
    Args:
        path: File path to write to
        content: Content to write
        overwrite: If False (default), will error if file exists.
                   Set to True only for intentional overwrites.
    """
    import time
    import shutil
    
    logger = logging.getLogger("SprintRunner")
    
    try:
        # Check if file exists
        if os.path.exists(path) and not overwrite:
            return f"Error: File '{path}' already exists. Use overwrite=True to replace it, or use a different filename."
        
        # Create backup if overwriting
        # (DISABLED: User request to avoid clutter)
        # if os.path.exists(path) and overwrite:
        #     backup_path = f"{path}.backup.{int(time.time())}"
        #     shutil.copy2(path, backup_path)
        #     logger.warning(f"[OVERWRITE] Backed up {path} to {backup_path}")
        
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"

@log_tool_usage
def run_command(command: str):
    """Executes a shell command and returns the output."""
    try:
        # Helper to fix common cross-platform command issues
        if "mkdir -p" in command:
            # On Windows, 'mkdir' creates intermediates by default (in cmd) but 'mkdir -p' fails.
            # In PowerShell 'mkdir' is a function 'md'.
            # We can strip '-p'.
            command = command.replace("mkdir -p", "mkdir")
            
        logger = logging.getLogger("SprintRunner")
        logger.info(f"[Tool:run_command] Executing: {command}")
        
        # PAGER=cat to avoid hanging on long output
        env = os.environ.copy()
        env["PAGER"] = "cat"
        # Force non-interactive modes
        env["CI"] = "true"
        env["npm_config_yes"] = "true" 
        env["PIP_NO_INPUT"] = "1"
        env["NON_INTERACTIVE"] = "true"
        # Timeout added to prevent hangs
        result = subprocess.run(command, shell=True, capture_output=True, text=True, env=env, timeout=30)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except Exception as e:
        return f"Error: {e}"


@log_async_tool_usage
async def update_sprint_header(status: str, sprint_dir: str = "project_tracking"):
    """
    Updates the Sprint Status header in the latest sprint file.
    
    Args:
        status (str): The new status (e.g., "In Progress", "QA", "Review").
        sprint_dir (str): Directory containing sprint files.
    """
    import asyncio
    import msvcrt
    
    # Fix for path if not absolute
    if not os.path.isabs(sprint_dir):
         sprint_dir = os.path.abspath(os.path.join(os.getcwd(), sprint_dir))

    if not os.path.exists(sprint_dir):
        # Fallback to checking parent dir if running from scripts/
        parent_sprint_dir = os.path.join(os.path.dirname(os.getcwd()), "project_tracking")
        if os.path.exists(parent_sprint_dir):
            sprint_dir = parent_sprint_dir
        else:
             return f"Error: Sprint directory '{sprint_dir}' not found."

    sprint_files = [f for f in os.listdir(sprint_dir) if f.startswith("SPRINT_") and f.endswith(".md")]
    if not sprint_files:
        return "Error: No sprint files found."
    
    sprint_files.sort()
    latest_sprint = os.path.join(sprint_dir, sprint_files[-1])
    
    # Retry mechanism for file locking
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Use r+ mode for atomic read-modify-write
            with open(latest_sprint, "r+", encoding="utf-8") as f:
                try:
                    # Acquire exclusive lock
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                    
                    # Read and update
                    lines = f.readlines()
                    
                    updated_lines = []
                    found = False
                    for line in lines:
                        if "**Status**:" in line:
                            #Preserve indentation if any, though header usually has none
                            new_line = re.sub(r"\*\*Status\*\*: .*", f"**Status**: {status}", line)
                            updated_lines.append(new_line)
                            found = True
                        else:
                            updated_lines.append(line)
                    
                    if found:
                        # Write atomically
                        f.seek(0)
                        f.writelines(updated_lines)
                        f.truncate()
                        
                        return f"Successfully updated status to '{status}' in {latest_sprint}"
                    else:
                        return f"Status header not found in {latest_sprint}"
                
                finally:
                    # Always unlock
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except:
                        pass
        
        except IOError as e:
            # Lock contention
            if attempt < max_retries - 1:
                wait_time = 0.1 * (2 ** attempt)
                logger = logging.getLogger("SprintRunner")
                logger.debug(f"Lock contention on attempt {attempt + 1}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                return f"Error: Failed to update status after {max_retries} attempts: {e}"
        except Exception as e:
            return f"Error updating sprint file: {e}"
    
    return "Error: Failed to update status"

@log_async_tool_usage
async def update_sprint_task_status(task_description: str, status: str = "[x]", sprint_dir: str = "project_tracking"):
    """
    Updates the status of a specific task in the latest sprint file.
    Uses file locking to prevent race conditions during concurrent updates.
    
    Args:
        task_description (str): The text description of the task (without the - [ ] part).
        status (str): The new status checkmark, e.g., "[x]".
        sprint_dir (str): Directory containing sprint files.
    """

    import asyncio
    import msvcrt
    
    # Fix for path if not absolute
    if not os.path.isabs(sprint_dir):
         sprint_dir = os.path.abspath(os.path.join(os.getcwd(), sprint_dir))

    if not os.path.exists(sprint_dir):
        # Fallback to checking parent dir if running from scripts/
        parent_sprint_dir = os.path.join(os.path.dirname(os.getcwd()), "project_tracking")
        if os.path.exists(parent_sprint_dir):
            sprint_dir = parent_sprint_dir
        else:
             return f"Error: Sprint directory '{sprint_dir}' not found."

    sprint_files = [f for f in os.listdir(sprint_dir) if f.startswith("SPRINT_") and f.endswith(".md")]
    if not sprint_files:
        return "Error: No sprint files found."
    
    sprint_files.sort()
    latest_sprint = os.path.join(sprint_dir, sprint_files[-1])
    
    # Retry mechanism for file locking
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Use r+ mode for atomic read-modify-write
            with open(latest_sprint, "r+", encoding="utf-8") as f:
                try:
                    # Acquire exclusive lock (Windows compatible)
                    # Lock 1 byte at position 0
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                    
                    # Read and update
                    lines = f.readlines()
                    
                    updated_lines = []
                    found = False
                    for line in lines:
                        if task_description in line and "- [" in line:
                            new_line = re.sub(r"- \[.\]", f"- {status}", line)
                            updated_lines.append(new_line)
                            found = True
                        else:
                            updated_lines.append(line)
                    
                    if found:
                        # Write atomically
                        f.seek(0)
                        f.writelines(updated_lines)
                        f.truncate()
                        
                        return f"Successfully updated task '{task_description}' to {status} in {latest_sprint}"
                    else:
                        return f"Task '{task_description}' not found in {latest_sprint}"
                
                finally:
                    # Always unlock
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except:
                        pass  # Unlocking may fail if file is closed
        
        except IOError as e:
            # Lock contention - retry with exponential backoff
            if attempt < max_retries - 1:
                wait_time = 0.1 * (2 ** attempt)  # Exponential backoff: 0.1, 0.2, 0.4, 0.8, 1.6s
                logger = logging.getLogger("SprintRunner")
                logger.debug(f"Lock contention on attempt {attempt + 1}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                return f"Error: Failed to update after {max_retries} attempts due to lock contention: {e}"
        
        except Exception as e:
            return f"Error updating sprint file: {e}"
    
    return f"Error: Failed to update task '{task_description}' after {max_retries} attempts"


@log_async_tool_usage
async def add_sprint_task(role: str, task_description: str, sprint_dir: str = "project_tracking"):
    """
    Adds a new task to the latest sprint file under the specified role section.
    Args:
        role (str): The role section to add to (e.g., "Backend", "Frontend").
        task_description (str): The description of the new task.
        sprint_dir (str): Directory containing sprint files.
    """
    # Fix for path
    if not os.path.isabs(sprint_dir):
         sprint_dir = os.path.abspath(os.path.join(os.getcwd(), sprint_dir))

    if not os.path.exists(sprint_dir):
        parent_sprint_dir = os.path.join(os.path.dirname(os.getcwd()), "project_tracking")
        if os.path.exists(parent_sprint_dir):
            sprint_dir = parent_sprint_dir
        else:
             return f"Error: Sprint directory '{sprint_dir}' not found."

    sprint_files = [f for f in os.listdir(sprint_dir) if f.startswith("SPRINT_") and f.endswith(".md")]
    if not sprint_files:
        return "Error: No sprint files found."
    
    sprint_files.sort()
    latest_sprint = os.path.join(sprint_dir, sprint_files[-1])
    
    try:
        with open(latest_sprint, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        updated_lines = []
        role_found = False
        
        # Simple heuristic: Find header "### ... @Role ..." and verify we are in that block
        # Or just append to end if not found? 
        # Safer: Find the section header.
        
        for i, line in enumerate(lines):
            updated_lines.append(line)
            # Check if this line is the header for the role
            # Flexible match: "### @Backend" or "### Backend"
            if f"@{role}" in line and "###" in line:
                role_found = True
                # Insert the task after the header
                updated_lines.append(f"- [ ] {task_description}\n")
        
        if not role_found:
            # If role not found, append a new section at the end
            updated_lines.append(f"\n### {role} Tasks\n")
            updated_lines.append(f"- [ ] {task_description}\n")

        with open(latest_sprint, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
            
        return f"Successfully added task to {latest_sprint}"

    except Exception as e:
        return f"Error adding task: {e}"

@log_tool_usage
def search_codebase(pattern: str, root_dir: str = "."):
    """
    Recursively searches for a regex pattern in files within the root_dir.
    Ignores .git, __pycache__, and other common ignore dirs.
    """
    results = []
    ignore_dirs = {
        ".git", "__pycache__", ".venv", "node_modules", "dist", "build", "logs", 
        ".idea", ".vscode", "coverage", ".pytest_cache", "target", "bin", "obj"
    }
    
    try:
        regex = re.compile(pattern)
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if file.endswith((".log", ".lock", ".map", ".min.js", ".min.css", ".svg")):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if regex.search(line):
                                results.append(f"{file_path}:{i+1}: {line.strip()}")
                except Exception:
                    # distinct failure for single file read shouldn't abort search
                    continue
        
        if not results:
            return "No matches found."
        return "\n".join(results[:100]) # Limit results to prevent context overflow
        
    except Exception as e:
        return f"Error executing search: {e}"

@log_tool_usage
def discover_project_context(root_dir: str = "."):
    """
    Analyzes the project directory to detect tech stack, frameworks, and code patterns.
    Returns a structured summary of the project's technology choices.
    
    Args:
        root_dir: Root directory of the project to analyze
        
    Returns:
        JSON string with project context including tech_stack, frameworks, languages, etc.
    """
    import json
    import glob
    
    context = {
        "tech_stack": [],
        "frameworks": [],
        "package_managers": [],
        "key_files": [],
        "languages": {}
    }
    
    try:
        # Detect package managers and tech stack
        if os.path.exists(os.path.join(root_dir, "package.json")):
            context["package_managers"].append("npm/yarn")
            context["tech_stack"].append("Node.js")
            context["key_files"].append("package.json")
            try:
                with open(os.path.join(root_dir, "package.json"), "r", encoding="utf-8") as f:
                    pkg = json.loads(f.read())
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "express" in deps:
                        context["frameworks"].append("Express.js")
                    if "react" in deps:
                        context["frameworks"].append("React")
                    if "next" in deps:
                        context["frameworks"].append("Next.js")
                    if "vue" in deps:
                        context["frameworks"].append("Vue.js")
                    if "@angular/core" in deps:
                        context["frameworks"].append("Angular")
            except:
                pass
        
        if os.path.exists(os.path.join(root_dir, "requirements.txt")):
            context["package_managers"].append("pip")
            context["tech_stack"].append("Python")
            context["key_files"].append("requirements.txt")
        
        if os.path.exists(os.path.join(root_dir, "pyproject.toml")):
            context["package_managers"].append("poetry")
            if "Python" not in context["tech_stack"]:
                context["tech_stack"].append("Python")
            context["key_files"].append("pyproject.toml")
        
        # Check for .NET projects
        csproj_files = glob.glob(os.path.join(root_dir, "*.csproj"))
        if csproj_files:
            context["tech_stack"].append(".NET")
            context["key_files"].extend([os.path.basename(f) for f in csproj_files[:3]])
        
        # Check for Go
        if os.path.exists(os.path.join(root_dir, "go.mod")):
            context["tech_stack"].append("Go")
            context["key_files"].append("go.mod")
        
        # Check for Ruby
        if os.path.exists(os.path.join(root_dir, "Gemfile")):
            context["tech_stack"].append("Ruby")
            context["key_files"].append("Gemfile")
        
        # Count file types to determine primary language
        ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", "logs"}
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            # Limit depth to avoid scanning too deep
            if root.count(os.sep) - root_dir.count(os.sep) > 3:
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in [".js", ".jsx", ".ts", ".tsx"]:
                    context["languages"]["JavaScript/TypeScript"] = context["languages"].get("JavaScript/TypeScript", 0) + 1
                elif ext == ".py":
                    context["languages"]["Python"] = context["languages"].get("Python", 0) + 1
                elif ext == ".cs":
                    context["languages"]["C#"] = context["languages"].get("C#", 0) + 1
                elif ext in [".go"]:
                    context["languages"]["Go"] = context["languages"].get("Go", 0) + 1
                elif ext == ".rb":
                    context["languages"]["Ruby"] = context["languages"].get("Ruby", 0) + 1
                elif ext in [".java"]:
                    context["languages"]["Java"] = context["languages"].get("Java", 0) + 1
        
        # Determine primary language
        if context["languages"]:
            primary_lang = max(context["languages"].items(), key=lambda x: x[1])
            context["primary_language"] = primary_lang[0]
        
        return json.dumps(context, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to discover context: {e}"}, indent=2)

@log_async_tool_usage
async def enrich_task_context(task_description: str, context_data: dict, sprint_dir: str = "project_tracking"):
    """
    Adds technical context to a task in the sprint file as an HTML comment.
    This context persists across sprint interruptions and helps with resume.
    
    Args:
        task_description: The task description to enrich
        context_data: Dict with keys like 'tech_stack', 'related_files', 'patterns', 'dependencies'
        sprint_dir: Directory containing sprint files
    """
    import asyncio
    import msvcrt
    import json
    
    if not os.path.isabs(sprint_dir):
        sprint_dir = os.path.abspath(os.path.join(os.getcwd(), sprint_dir))
    
    if not os.path.exists(sprint_dir):
        return f"Error: Sprint directory '{sprint_dir}' not found."
    
    sprint_files = [f for f in os.listdir(sprint_dir) if f.startswith("SPRINT_") and f.endswith(".md")]
    if not sprint_files:
        return "Error: No sprint files found."
    
    sprint_files.sort()
    latest_sprint = os.path.join(sprint_dir, sprint_files[-1])
    
    # Build context comment
    context_lines = ["  <!-- CONTEXT"]
    if 'tech_stack' in context_data:
        context_lines.append(f"  Tech Stack: {context_data['tech_stack']}")
    if 'related_files' in context_data:
        context_lines.append(f"  Related Files: {context_data['related_files']}")
    if 'patterns' in context_data:
        context_lines.append(f"  Patterns: {context_data['patterns']}")
    if 'dependencies' in context_data:
        context_lines.append(f"  Dependencies: {context_data['dependencies']}")
    context_lines.append("  -->")
    context_block = "\n".join(context_lines)
    
    # Retry mechanism for file locking
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with open(latest_sprint, "r+", encoding="utf-8") as f:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                    
                    lines = f.readlines()
                    updated_lines = []
                    found = False
                    
                    for i, line in enumerate(lines):
                        updated_lines.append(line)
                        
                        # If this line contains the task and doesn't already have context
                        if task_description in line and "- [" in line:
                            # Check if next line is already a context comment
                            if i + 1 < len(lines) and "<!-- CONTEXT" in lines[i + 1]:
                                continue  # Skip, already has context
                            
                            # Add context block after the task line
                            updated_lines.append(context_block + "\n")
                            found = True
                    
                    if found:
                        f.seek(0)
                        f.writelines(updated_lines)
                        f.truncate()
                        return f"Successfully enriched task '{task_description}' with context"
                    else:
                        return f"Task '{task_description}' not found or already has context"
                
                finally:
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except:
                        pass
        
        except IOError as e:
            if attempt < max_retries - 1:
                wait_time = 0.1 * (2 ** attempt)
                logger = logging.getLogger("SprintRunner")
                logger.debug(f"Lock contention on attempt {attempt + 1}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                return f"Error: Failed to enrich after {max_retries} attempts: {e}"
        except Exception as e:
            return f"Error enriching task: {e}"
    
    return "Error: Failed to enrich task"

# --- Turn Budget Management Tools ---

from sprint_metadata import parse_task_metadata, update_task_metadata_in_file

@log_tool_usage
def request_turn_budget(task_description: str, estimated_turns: int, justification: str) -> dict:
    """
    Agent requests turn budget for a task they're about to execute.
    
    Args:
        task_description: The task being estimated
        estimated_turns: Number of turns agent thinks it needs (minimum 20)
        justification: Why this many turns are needed
    
    Returns:
        Approved turn budget
    """
    from sprint_config import SprintConfig
    
    # Enforce minimum
    approved_turns = max(20, estimated_turns)
    
    # Update task in sprint file with metadata
    sprint_file = detect_latest_sprint_file(SprintConfig.get_sprint_dir())
    updated = update_task_metadata_in_file(
        sprint_file,
        task_description,
        {"TURNS_ESTIMATED": approved_turns}
    )
    
    return {
        "task": task_description[:60],
        "requested": estimated_turns,
        "approved": approved_turns,
        "justification": justification,
        "status": "approved" if updated else "warning: task not found in sprint file"
    }


@log_tool_usage
def record_turn_usage(task_description: str, turns_used: int) -> dict:
    """
    Record actual turns used after task completion.
    Called automatically by runner.
    
    Args:
        task_description: The completed task
        turns_used: Actual number of turns consumed
    
    Returns:
        Confirmation of recording
    """
    from sprint_config import SprintConfig
    
    sprint_file = detect_latest_sprint_file(SprintConfig.get_sprint_dir())
    updated = update_task_metadata_in_file(
        sprint_file,
        task_description,
        {"TURNS_USED": turns_used}
    )
    
    logger = logging.getLogger("SprintRunner")
    logger.info(f"[Turn Tracking] Task used {turns_used} turns")
    
    return {
        "task": task_description[:60],
        "turns_used": turns_used,
        "status": "recorded" if updated else "error: task not found"
    }


@log_tool_usage
def analyze_turn_metrics(sprint_file: str = None) -> dict:
    """
    Analyze turn usage vs. story points for retrospective.
    
    Args:
        sprint_file: Path to sprint file (optional, uses current if not provided)
    
    Returns:
        Statistics and insights about turn usage
    """
    from sprint_config import SprintConfig
    from sprint_utils import get_all_sprint_tasks
    
    if not sprint_file:
        sprint_file = detect_latest_sprint_file(SprintConfig.get_sprint_dir())
    
    tasks = get_all_sprint_tasks(sprint_file)
    
    stats = {
        "tasks_analyzed": 0,
        "avg_points": 0,
        "avg_turns_used": 0,
        "avg_turns_per_point": 0,
        "underestimated": [],
        "overestimated": [],
        "accurate": [],
        "details": []
    }
    
    analyzed = []
    for task in tasks:
        points = parse_task_metadata(task.get('desc', ''), 'POINTS')
        used = parse_task_metadata(task.get('desc', ''), 'TURNS_USED')
        estimated = parse_task_metadata(task.get('desc', ''), 'TURNS_ESTIMATED')
        
        if points and used:
            variance = ((used - estimated) / estimated * 100) if estimated else 0
            
            analyzed.append({
                'task': task['desc'][:60],
                'role': task.get('role'),
                'points': points,
                'estimated': estimated or 'N/A',
                'used': used,
                'variance': f"{variance:.1f}%" if estimated else 'N/A'
            })
            
            if estimated and variance > 25:
                stats['underestimated'].append(task['desc'][:60])
            elif estimated and variance < -25:
                stats['overestimated'].append(task['desc'][:60])
            elif estimated:
                stats['accurate'].append(task['desc'][:60])
    
    if analyzed:
        stats['tasks_analyzed'] = len(analyzed)
        total_points = sum(t['points'] for t in analyzed)
        total_turns = sum(t['used'] for t in analyzed)
        
        stats['avg_points'] = round(total_points / len(analyzed), 1)
        stats['avg_turns_used'] = round(total_turns / len(analyzed), 1)
        stats['avg_turns_per_point'] = round(total_turns / total_points, 1) if total_points else 0
        stats['details'] = analyzed
    
    return stats


# Tool Definitions for Agent Consumption
worker_tools = [
                     FunctionTool(list_dir),
                     FunctionTool(read_file),
                     FunctionTool(write_file),
                     FunctionTool(run_command),
                     FunctionTool(search_codebase),
                     FunctionTool(discover_project_context),
                     FunctionTool(enrich_task_context),
                     FunctionTool(request_turn_budget),
                     FunctionTool(record_turn_usage)
]

orchestrator_tools = [FunctionTool(update_sprint_task_status)]

qa_tools = worker_tools + [FunctionTool(add_sprint_task)]

pm_tools = worker_tools + [FunctionTool(add_sprint_task), FunctionTool(analyze_turn_metrics)]
