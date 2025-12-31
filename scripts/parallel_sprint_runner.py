import asyncio
import os
import re
from google.adk.agents import LlmAgent, InvocationContext
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

# Import Config and Modules
from sprint_config import SprintConfig
from sprint_tools import worker_tools, orchestrator_tools, update_sprint_task_status, search_codebase
from sprint_utils import detect_latest_sprint_file, parse_sprint_tasks

async def main():
    # Validate Config
    SprintConfig.validate()
    
    # 1. Detect Sprint
    latest_sprint = detect_latest_sprint_file(SprintConfig.SPRINT_DIR)
    if not latest_sprint:
        print(f"No sprint files found in {SprintConfig.SPRINT_DIR}")
        return
    
    print(f"[*] Analyzing {latest_sprint} for parallel tasks...")

    # 2. Parse Tasks
    tasks_to_execute = parse_sprint_tasks(latest_sprint)
    if not tasks_to_execute:
        print("No pending tasks found in the latest sprint.")
        return

    print(f"[*] Found {len(tasks_to_execute)} tasks to execute in parallel.")

    # 3. Setup Session Service
    session_service = InMemorySessionService()

    # 4. Initialize Orchestrator
    print("[*] Initializing Orchestrator Agent...")
    orchestrator_prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_orchestrator.md")
    framework_index_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_framework_index.md")
    
    framework_instruction = ""
    if os.path.exists(framework_index_path):
        with open(framework_index_path, "r", encoding="utf-8") as f:
            framework_instruction = f.read()

    if os.path.exists(orchestrator_prompt_path):
        with open(orchestrator_prompt_path, "r", encoding="utf-8") as f:
            orchestrator_instruction = f.read()
    else:
        orchestrator_instruction = "You are the Orchestrator."
    
    # Prepend Framework Instructions
    orchestrator_instruction = f"{framework_instruction}\n\n{orchestrator_instruction}"

    orchestrator_agent = LlmAgent(
        name="Orchestrator",
        instruction=orchestrator_instruction,
        model=SprintConfig.MODEL_NAME,
        tools=orchestrator_tools
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


    # 5. Worker Logic
    concurrency_limit = SprintConfig.CONCURRENCY_LIMIT
    sem = asyncio.Semaphore(concurrency_limit)
    print(f"[*] Starting parallel execution (Concurrency limit: {concurrency_limit})...")
    
    role_map = SprintConfig.get_role_map()

    async def run_task(task_info, task_index):
        async with sem:
            role_raw = task_info["role"]
            role = role_raw.lower()
            desc = task_info["desc"]
            
            print(f"\n    [Task {task_index+1}] Starting @{role_raw}: {desc}")
            
            # --- ORCHESTRATOR: MARK IN PROGRESS ---
            await invoke_orchestrator_update(desc, role_raw, status_instruction="mark it as in-progress ([/])")
            
            prompt_file = role_map.get(role_raw, "agent_orchestrator.md")
            prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, prompt_file)
            
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    instruction = f.read()
            else:
                instruction = f"Act as {role}."

            # Prepend Framework Instructions for Workers too
            full_instruction = f"{framework_instruction}\n\n{instruction}"

            sanitized_role = re.sub(r'[^a-zA-Z0-9_]', '', role)
            agent_name = f"{sanitized_role}_{task_index}"
            
            agent = LlmAgent(
                name=agent_name,
                instruction=f"{full_instruction}\n\nTask: {desc}",
                model=SprintConfig.MODEL_NAME,
                tools=worker_tools
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
                # Basic check for rate limits
                msg = str(e).lower()
                if "resource" in msg and "exhausted" in msg:
                    print(f"    [Task {task_index+1}] [RetryCheck] Rate limit detected. Retrying...")
                    return True
                if "429" in msg:
                    print(f"    [Task {task_index+1}] [RetryCheck] 429 detected. Retrying...")
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

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        # In production, logging to file is good, simplified here for now.
