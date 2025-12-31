import asyncio
import os
import re
from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.getcwd(), ".env"))
print(f"DEBUG: CWD: {os.getcwd()}")
print(f"DEBUG: GOOGLE_API_KEY found: {bool(os.environ.get('GOOGLE_API_KEY'))}")
from google.adk.agents import LlmAgent, ParallelAgent, InvocationContext
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
import subprocess
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, retry_if_exception

def list_dir(path: str = "."):
    """Lists files and directories in the specified path."""
    try:
        return os.listdir(path)
    except Exception as e:
        return f"Error: {e}"

def read_file(path: str):
    """Reads the content of a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

def write_file(path: str, content: str):
    """Writes content to a file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"

def run_command(command: str):
    """Executes a shell command and returns the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except Exception as e:
        return f"Error: {e}"

async def update_sprint_task_status(task_description: str, status: str = "[x]"):
    """
    Updates the status of a specific task in the latest sprint file.
    Args:
        task_description (str): The text description of the task (without the - [ ] part).
        status (str): The new status checkmark, e.g., "[x]".
    """
    sprint_dir = "project_tracking"
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
            # Check if this line contains the task description
            # We look for "- [ ] task_description" or "- [x] task_description"
            # We want to match loosely to account for formatting
            if task_description in line and "- [" in line:
                # Replace the bracket part
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

def parse_sprint_tasks(sprint_file_path):
    """
    Parses the Task Breakdown section of a sprint markdown file.
    Returns a list of tasks with role and description.
    """
    tasks = []
    if not os.path.exists(sprint_file_path):
        print(f"Error: Sprint file {sprint_file_path} not found.")
        return tasks

    with open(sprint_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for the Task Breakdown section
    sections = re.split(r"### ", content)
    for section in sections:
        lines = section.split("\n")
        header = lines[0]
        # Identify roles in the header (e.g., @Backend @Security)
        roles = re.findall(r"@(\w+)", header)
        if not roles:
            continue

        for line in lines[1:]:
            # Match todo items: - [ ] Task description
            match = re.search(r"- \[ \] (.*)", line)
            if match:
                desc = match.group(1).strip()
                # For simplicity, assign to the first role mentioned in the section
                tasks.append({"role": roles[0], "desc": desc})
    
    return tasks

async def main():
    # Detect latest sprint file
    sprint_dir = "project_tracking"
    sprint_files = [f for f in os.listdir(sprint_dir) if f.startswith("SPRINT_") and f.endswith(".md")]
    if not sprint_files:
        print("No sprint files found.")
        return
    
    sprint_files.sort()
    latest_sprint = os.path.join(sprint_dir, sprint_files[-1])
    print(f"[*] Analyzing {latest_sprint} for parallel tasks...")

    # Parse tasks
    tasks_to_execute = parse_sprint_tasks(latest_sprint)
    if not tasks_to_execute:
        print("No pending tasks found in the latest sprint.")
        return

    print(f"[*] Found {len(tasks_to_execute)} tasks to execute in parallel.")

    # ADK Imports and Session Setup
    session_service = InMemorySessionService()
    
    # Prompt base directory
    prompt_base = r"C:\Users\Michael\.gemini\.agent\prompts"
    
    # Map roles to prompt files
    role_map = {
        "Backend": "agent_backend.md",
        "Frontend": "agent_frontend.md",
        "DevOps": "agent_devops.md",
        "QA": "agent_qa.md",
        "Security": "agent_security.md",
        "PM": "agent_product_management.md"
    }

    # Initialize Orchestrator Agent
    print("[*] Initializing Orchestrator Agent...")
    orchestrator_prompt_path = os.path.join(prompt_base, "agent_orchestrator.md")
    if os.path.exists(orchestrator_prompt_path):
        with open(orchestrator_prompt_path, "r", encoding="utf-8") as f:
            orchestrator_instruction = f.read()
    else:
        orchestrator_instruction = "You are the Orchestrator."

    orchestrator_agent = LlmAgent(
        name="Orchestrator",
        instruction=orchestrator_instruction,
        model="gemini-3-flash-preview",
        tools=[FunctionTool(update_sprint_task_status)]
    )
    
    await session_service.create_session(
        app_name="SprintRunner",
        user_id="user",
        session_id="orchestrator_session"
    )
    
    orchestrator_runner = Runner(
        app_name="SprintRunner",
        agent=orchestrator_agent,
        session_service=session_service
    )
    
    orchestrator_lock = asyncio.Lock()

    async def invoke_orchestrator_update(task_desc, role, status_instruction):
        async with orchestrator_lock:
            print(f"    [Orchestrator] Request: {status_instruction} for task: {task_desc}")
            try:
                # We reuse the same session for the orchestrator
                user_msg = f"The {role} Agent has valid update for task: '{task_desc}'. Please {status_instruction} in the sprint file."
                
                async for event in orchestrator_runner.run_async(
                    user_id="user",
                    session_id="orchestrator_session",
                    new_message=types.Content(parts=[types.Part(text=user_msg)]),
                    invocation_id=None
                ):
                     if event.content and event.content.parts:
                        for part in event.content.parts:
                            if getattr(part, 'function_call', None):
                                print(f"    [Orchestrator ToolCall] {part.function_call.name}")
                            if getattr(part, 'function_response', None):
                                print(f"    [Orchestrator ToolResponse] {part.function_response.name}")

            except Exception as e:
                 print(f"    [Orchestrator Error] {e}")


    # Worker Logic
    concurrency_limit = 3
    sem = asyncio.Semaphore(concurrency_limit)
    print(f"[*] Starting parallel execution (Concurrency limit: {concurrency_limit})...")
    
    async def run_task(task_info, task_index):
        async with sem:
            role_raw = task_info["role"]
            role = role_raw.lower()
            desc = task_info["desc"]
            
            print(f"\n    [Task {task_index+1}] Starting @{role_raw}: {desc}")
            
            # --- ORCHESTRATOR: MARK IN PROGRESS ---
            await invoke_orchestrator_update(desc, role_raw, status_instruction="mark it as in-progress ([/])")
            
            prompt_file = role_map.get(role_raw, "agent_orchestrator.md")
            prompt_path = os.path.join(prompt_base, prompt_file)
            
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    instruction = f.read()
            else:
                instruction = f"Act as {role}."

            sanitized_role = re.sub(r'[^a-zA-Z0-9_]', '', role)
            agent_name = f"{sanitized_role}_{task_index}"
            
            agent = LlmAgent(
                name=agent_name,
                instruction=f"{instruction}\n\nTask: {desc}",
                model="gemini-3-flash-preview",
                tools=[
                    FunctionTool(list_dir),
                    FunctionTool(read_file),
                    FunctionTool(write_file),
                    FunctionTool(run_command)
                ]
            )

            worker_session_id = f"worker_session_{task_index}"
            await session_service.create_session(
                app_name="SprintRunner",
                user_id="user",
                session_id=worker_session_id
            )

            runner = Runner(
                app_name="SprintRunner",
                agent=agent,
                session_service=session_service
            )

            def retry_predicate(e):
                print(f"    [Task {task_index+1}] [RetryCheck] Exception: {type(e)}")
                is_429 = False
                if "_ResourceExhaustedError" in str(type(e)) or "429" in str(e):
                    is_429 = True
                
                if isinstance(e, ExceptionGroup):
                    if any("_ResourceExhaustedError" in str(type(sub)) or "429" in str(sub) for sub in e.exceptions):
                        is_429 = True
                
                if is_429:
                    print(f"    [Task {task_index+1}] [RetryCheck] Rate limit detected. Retrying...")
                    return True
                return False

            @retry(
                wait=wait_exponential(multiplier=30, min=30, max=300),
                stop=stop_after_attempt(5),
                retry=retry_if_exception(retry_predicate),
                reraise=True
            )
            async def run_with_retry():
                try:
                    async for event in runner.run_async(
                        user_id="user",
                        session_id=worker_session_id,
                        new_message=types.Content(parts=[types.Part(text="Execute this task.")]),
                        invocation_id=None
                    ):
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if part.text:
                                    print(f"    [{event.author}] {part.text.strip()}")
                                
                                if getattr(part, 'function_call', None):
                                    print(f"    [ToolCall] {event.author} calling {part.function_call.name} with {part.function_call.args}")
                                
                                if getattr(part, 'function_response', None):
                                    print(f"    [ToolResponse] {event.author} received from {part.function_response.name}")

                except Exception as e:
                    print(f"    [Error] {agent_name}: {type(e)}")
                    raise e

            try:
                await run_with_retry()
                print(f"    [Task {task_index+1}] Completed @{role_raw}")
                # --- ORCHESTRATOR: MARK DONE ---
                await invoke_orchestrator_update(desc, role_raw, status_instruction="mark it as completed ([x])")
            except Exception as e:
                print(f"    [Task {task_index+1}] FAILED @{role_raw}")
                # --- ORCHESTRATOR: MARK BLOCKED ---
                await invoke_orchestrator_update(desc, role_raw, status_instruction="mark it as blocked ([!]) because it failed.")


    tasks = [run_task(task, idx) for idx, task in enumerate(tasks_to_execute)]
    await asyncio.gather(*tasks)
    
    print(f"\n[SprintRunner] Mission execution complete.")
    
    print(f"\n[ParallelAgent] Sprint execution complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        with open("error_log.txt", "w") as f:
            f.write(f"Type: {type(e)}\n")
            f.write(f"Error: {str(e)}\n")
            
            if isinstance(e, ExceptionGroup):
                f.write(f"\nSub-exceptions ({len(e.exceptions)}):\n")
                for i, sub_e in enumerate(e.exceptions):
                    f.write(f"\n[{i}] {type(sub_e)}: {sub_e}\n")
                    if hasattr(sub_e, 'errors'):
                         import json
                         f.write(json.dumps(sub_e.errors(), indent=2))
            
            if hasattr(e, 'errors'):
                import json
                f.write("\nPydantic Errors:\n")
                f.write(json.dumps(e.errors(), indent=2))
        print("CRITICAL ERROR logged to error_log.txt")
