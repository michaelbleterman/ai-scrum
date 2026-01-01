import os
import re
import subprocess
import logging
import functools
from google.adk.tools import FunctionTool

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
def write_file(path: str, content: str):
    """Writes content to a file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"

@log_tool_usage
def run_command(command: str):
    """Executes a shell command and returns the output."""
    try:
        # PAGER=cat to avoid hanging on long output
        env = os.environ.copy()
        env["PAGER"] = "cat"
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
async def update_sprint_task_status(task_description: str, status: str = "[x]", sprint_dir: str = "project_tracking"):
    """
    Updates the status of a specific task in the latest sprint file.
    Args:
        task_description (str): The text description of the task (without the - [ ] part).
        status (str): The new status checkmark, e.g., "[x]".
        sprint_dir (str): Directory containing sprint files.
    """
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
    
    try:
        with open(latest_sprint, "r", encoding="utf-8") as f:
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
            with open(latest_sprint, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)
            return f"Successfully updated task '{task_description}' to {status} in {latest_sprint}"
        else:
            return f"Task '{task_description}' not found in {latest_sprint}"

    except Exception as e:
        return f"Error updating sprint file: {e}"

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
    ignore_dirs = {".git", "__pycache__", ".venv", "node_modules", "dist", "build"}
    
    try:
        regex = re.compile(pattern)
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
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

# Tool Definitions for Agent Consumption
worker_tools = [
                     FunctionTool(list_dir),
                     FunctionTool(read_file),
                     FunctionTool(write_file),
                     FunctionTool(run_command),
                     FunctionTool(search_codebase)
]

orchestrator_tools = [FunctionTool(update_sprint_task_status)]

qa_tools = worker_tools + [FunctionTool(add_sprint_task)]
