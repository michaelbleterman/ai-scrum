import argparse
import asyncio
import os
import re
import sys
import traceback
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

# Import Config and Modules
from sprint_config import SprintConfig
from sprint_tools import worker_tools, orchestrator_tools, qa_tools, update_sprint_task_status
from sprint_utils import detect_latest_sprint_file, parse_sprint_tasks, get_all_sprint_tasks, analyze_sprint_status

import logging
from logging.handlers import RotatingFileHandler

# --- Logging Setup ---
def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "sprint_debug.log")
    
    # Create rotating file handler (20MB max, 5 backups = 100MB total)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=20 * 1024 * 1024,  # 20 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Format with timestamp
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger("SprintRunner")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

def log(msg):
    # Log to file and console via logger
    logger.info(msg)

def retry_predicate(exception):
    """
    Retry if the exception is a 429 Resource Exhausted or related rate limit error.
    """
    e_str = str(exception)
    if "429" in e_str or "ResourceExhausted" in e_str or "Quota exceeded" in e_str:
        log(f"    [Retry Trigger] Detected Rate Limit (429): {e_str[:100]}...")
        return True
    return False

retry_decorator = retry(
    wait=wait_exponential(multiplier=10, min=10, max=120), # Wait between 10s and 120s
    stop=stop_after_attempt(10), # Increase retries to 10 for deep backoff
    retry=retry_if_exception(retry_predicate),
    reraise=True
)

def default_agent_factory(name, instruction, tools, model=None, agent_role=None):
    """
    Create an LLM agent with optimal model selection.
    
    Args:
        name: Agent instance name
        instruction: Agent system prompt
        tools: Available tools for the agent
        model: Optional explicit model override
        agent_role: Agent role/type for automatic model selection (e.g., 'Backend', 'QA', 'Orchestrator')
    """
    if model is None:
        # Determine model based on agent role/name
        identifier = agent_role if agent_role else name
        model = SprintConfig.get_model_for_agent(identifier)
    
    logger.info(f"Creating agent '{name}' (role: {agent_role or 'unknown'}) with model: {model}")
    return LlmAgent(name=name, instruction=instruction, tools=tools, model=model)

# --- Phase 1: Parallel Execution ---
async def run_parallel_execution(session_service, framework_instruction, sprint_file, agent_factory=default_agent_factory):
    log("\n[Phase 1] Parallel Execution: Analyzing sprint status...")
    
    # Analyze sprint status before execution
    status_summary = analyze_sprint_status(sprint_file)
    log(f"    Sprint Status Summary:")
    log(f"      Total Tasks: {status_summary['total']}")
    log(f"      Completed: {status_summary.get('done', 0)}")
    log(f"      In-Progress: {status_summary['in_progress']}")
    log(f"      Blocked: {status_summary['blocked']}")
    log(f"      Todo: {status_summary['todo']}")
    
    if status_summary['blocked'] > 0:
        log(f"    Blocked Tasks:")
        for blocked_task in status_summary['blocked_tasks']:
            log(f"      - @{blocked_task['role']}: {blocked_task['desc']}")
    
    if status_summary['in_progress'] > 0:
        log(f"    In-Progress Tasks (will resume):")
        for in_prog_task in status_summary['in_progress_tasks']:
            log(f"      - @{in_prog_task['role']}: {in_prog_task['desc']}")
    
    log("\n    Checking for tasks to execute...")
    tasks_to_execute = parse_sprint_tasks(sprint_file)
    if not tasks_to_execute:
        log("    No pending tasks found.")
        return 0

    # Count tasks by status
    status_counts = {"todo": 0, "in_progress": 0, "blocked": 0}
    for task in tasks_to_execute:
        status_counts[task["status"]] += 1
    
    log(f"    Found {len(tasks_to_execute)} tasks to execute: {status_counts['todo']} Todo, {status_counts['in_progress']} In-Progress, {status_counts['blocked']} Blocked")
    
    concurrency_limit = SprintConfig.CONCURRENCY_LIMIT
    sem = asyncio.Semaphore(concurrency_limit)
    role_map = SprintConfig.get_role_map()

    async def run_single_task(task_info, task_index):
        async with sem:
            role_raw = task_info["role"]
            role = role_raw.lower()
            desc = task_info["desc"]
            status = task_info["status"]
            blocker_reason = task_info.get("blocker_reason")
            
            status_label = status.upper().replace('_', '-')
            log(f"\n    [Task {task_index+1}] Starting @{role_raw} [{status_label}]: {desc}")
            
            # DIRECT UPDATE: Mark in-progress
            try:
                await update_sprint_task_status(desc, "[/]", SprintConfig.get_sprint_dir())
            except Exception as e:
                log(f"    [Update Error] Failed to mark in-progress: {e}")

            prompt_file = role_map.get(role_raw, "agent_orchestrator.md")
            prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, prompt_file)
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    instruction = f.read()
            else:
                instruction = f"Act as {role}."

            agent_name = f"{re.sub(r'[^a-zA-Z0-9_]', '', role)}_{task_index}"
            full_instruction = f"{framework_instruction}\n\n{instruction}\n\nTask: {desc}"
            
            # Add status-specific instructions
            if status == "in_progress":
                resume_instruction = (
                    "\n\n=== RESUME NOTICE ===\n"
                    "This task is marked as IN_PROGRESS from a previous session.\n"
                    "Search for existing files, code, or partial work in the workspace before starting.\n"
                    "Resume where it left off if possible. Review any existing implementation.\n"
                    "==================="
                )
                full_instruction += resume_instruction
                log(f"    [Task {task_index+1}] Adding RESUME instruction")
            
            elif status == "blocked":
                unblock_instruction = (
                    "\n\n=== UNBLOCK NOTICE ===\n"
                    "This task was previously BLOCKED.\n"
                )
                if blocker_reason:
                    unblock_instruction += f"Previous blocker: {blocker_reason}\n"
                unblock_instruction += (
                    "Investigate the root cause, check logs, verify dependencies, and attempt to resolve the blocker.\n"
                    "If still blocked after investigation, document the reason clearly in your response.\n"
                    "======================"
                )
                full_instruction += unblock_instruction
                log(f"    [Task {task_index+1}] Adding UNBLOCK instruction" + (f" (Reason: {blocker_reason})" if blocker_reason else ""))
            
            agent = agent_factory(
                name=agent_name,
                instruction=full_instruction,
                tools=worker_tools,
                agent_role=role  # Pass role for optimal model selection
            )

            # Make session ID unique per cycle or delete previous?
            # Easiest: append random or cycle index if passed.
            # But run_parallel_execution doesn't know cycle count?
            # Actually, we can check if session exists.
            # But simpler: use random suffix or just handle the error.
            # Better: Pass cycle_index to run_parallel_execution.
            worker_pid = f"worker_{task_index}_{os.urandom(4).hex()}" 
            await session_service.create_session(
                app_name="SprintRunner", 
                user_id="user", 
                session_id=worker_pid
            )
            runner = Runner(
                app_name="SprintRunner", 
                agent=agent, 
                session_service=session_service
            )

            @retry_decorator
            async def run_agent():
                turn_count = 0
                max_turns = 20
                async for event in runner.run_async(
                    user_id="user", 
                    session_id=worker_pid, 
                    new_message=types.Content(parts=[types.Part(text=f"Execute this task: {desc}")])
                ):
                    turn_count += 1
                    if turn_count > max_turns:
                        msg = f"[Agent {role_raw}] EXCEEDED MAX TURNS ({max_turns}). Killing."
                        logger.error(msg)
                        print(msg) # Print to stdout for test capture
                        break

                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                msg = f"[Agent {role_raw}] Thought: {part.text}"
                                logger.info(msg)
                                print(msg)
                            if getattr(part, 'function_call', None):
                                msg = f"[Agent {role_raw}] Call: {part.function_call.name}({part.function_call.args})"
                                logger.info(msg)
                                print(msg)

            try:
                await run_agent()
                log(f"    [Task {task_index+1}] Completed @{role_raw}")
                # DIRECT UPDATE: Mark done
                await update_sprint_task_status(desc, "[x]", SprintConfig.get_sprint_dir())

            except Exception as e:
                log(f"    [Task {task_index+1}] FAILED @{role_raw}: {e}")
                # Mark as blocked if it fails
                await update_sprint_task_status(desc, "[!]", SprintConfig.get_sprint_dir())

    tasks = [run_single_task(task, idx) for idx, task in enumerate(tasks_to_execute)]
    await asyncio.gather(*tasks)
    return len(tasks_to_execute)

# --- Phase 2: QA & Validation ---
async def run_qa_phase(session_service, framework_instruction, sprint_file, agent_factory=default_agent_factory):
    log("\n[Phase 2] QA Verification: Validating completed tasks...")
    
    all_tasks = get_all_sprint_tasks(sprint_file)
    review_tasks = [t for t in all_tasks if t['status'] == 'done']
    
    if not review_tasks:
        log("    No tasks to review.")
        return False

    task_list_str = "\n".join([f"- {t['desc']} (@{t['role']})" for t in review_tasks])
    log(f"    Verifying {len(review_tasks)} tasks...")

    qa_prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_qa.md")
    if os.path.exists(qa_prompt_path):
        with open(qa_prompt_path, "r", encoding="utf-8") as f:
             qa_instruction = f.read()
    else:
        qa_instruction = "You are the QA Engineer."

    qa_full_instruction = (
        f"{framework_instruction}\n\n{qa_instruction}\n\nTasks to Verify:\n{task_list_str}\n\n"
        "INSTRUCTIONS:\n"
        "1. For each task, generate and run E2E/Playwright/Unit tests to verify it.\n"
        "2. If a task fails verification, use the `add_sprint_task` tool to create a NEW task with description starting with 'DEFECT: ...'.\n"
        "3. Write a summary report to 'project_tracking/QA_REPORT.md'.\n"
        "4. If all validations pass, explicitly state 'ALL PASSED' in your final response."
    )

    qa_agent = agent_factory(
        name="QA_Engineer",
        instruction=qa_full_instruction,
        tools=qa_tools,
        agent_role="QA"  # Use Pro model for comprehensive testing
    )

    qa_pid = f"qa_session_{os.urandom(4).hex()}"
    await session_service.create_session(
        app_name="SprintRunner", 
        user_id="user", 
        session_id=qa_pid
    )
    runner = Runner(
        app_name="SprintRunner", 
        agent=qa_agent, 
        session_service=session_service
    )
    
    defects_created = False
    
    @retry_decorator
    async def run_qa():
        nonlocal defects_created
        async for event in runner.run_async(
            user_id="user", 
            session_id=qa_pid, 
            new_message=types.Content(parts=[types.Part(text="Begin QA verification.")])
        ):
             if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        logger.info(f"[QA] Thought: {part.text}")
                    if getattr(part, 'function_call', None):
                        logger.info(f"[QA] Call: {part.function_call.name}({part.function_call.args})")
                        if part.function_call.name == "add_sprint_task":
                            defects_created = True

    await run_qa()
    
    if defects_created:
        log("    [QA] Defects were found and added to the sprint.")
        return True
    
    log("    [QA] Verification complete. No new defects reported.")
    return False

# --- Phase 3: Demo ---
async def run_demo_phase(session_service, framework_instruction, sprint_file, agent_factory=default_agent_factory, input_callback=None):
    log("\n[Phase 3] Demo & Feedback")
    
    orchestrator_agent = agent_factory(
        name="Orchestrator",
        instruction=f"{framework_instruction}\n\nYou are the Orchestrator. Goal: Prepare a Demo Walkthrough.\n"
                    "1. Read the 'project_tracking/QA_REPORT.md'.\n"
                    "2. Read the latest sprint file.\n"
                    "3. Generate a 'project_tracking/DEMO_WALKTHROUGH.md' summarizing what was built and how to use it.\n",
        tools=worker_tools,
        agent_role="Orchestrator"  # Use Pro model for coordination
    )
    
    await session_service.create_session(
        app_name="SprintRunner", 
        user_id="user", 
        session_id="demo_session"
    )
    runner = Runner(
        app_name="SprintRunner", 
        agent=orchestrator_agent, 
        session_service=session_service
    )
    
    @retry_decorator
    async def run_demo():
        async for event in runner.run_async(
            user_id="user", 
            session_id="demo_session", 
            new_message=types.Content(parts=[types.Part(text="Create the demo walkthrough.")])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        logger.info(f"[Orchestrator] Thought: {part.text}")
                    if getattr(part, 'function_call', None):
                        logger.info(f"[Orchestrator] Call: {part.function_call.name}({part.function_call.args})")

    await run_demo()
    
    log("    Demo Walkthrough generated: project_tracking/DEMO_WALKTHROUGH.md")
    log("    [ACTION REQUIRED] Please review the demo file.")
    
    feedback = ""
    # Capture Feedback
    if input_callback:
        feedback = input_callback("    Feedback: > ")
    else:
        try:
            if os.environ.get("NON_INTERACTIVE"):
                feedback = "No feedback provided (Non-interactive mode)."
            else:
                print("    >> Please enter your feedback for this sprint (or press Enter to skip):")
                feedback = input("    Feedback: > ")
        except EOFError:
            feedback = "No feedback provided (EOF)."
        
    return feedback

# --- Phase 4: Retro ---
async def run_retro_phase(session_service, framework_instruction, sprint_file, demo_feedback, agent_factory=default_agent_factory):
    log("\n[Phase 4] Retrospective")
    
    pm_prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_product_management.md")
    if os.path.exists(pm_prompt_path):
        with open(pm_prompt_path, "r", encoding="utf-8") as f:
             pm_instruction = f.read()
    else:
        pm_instruction = "You are the Product Manager."

    user_feedback_section = f"\nUser Feedback from Demo: {demo_feedback}\n" if demo_feedback else "\nUser Feedback from Demo: None provided.\n"

    pm_full_instruction = (
        f"{framework_instruction}\n\n{pm_instruction}\n\n"
        f"{user_feedback_section}\n"
        "INSTRUCTIONS:\n"
        "1. Read 'project_tracking/QA_REPORT.md' and 'project_tracking/DEMO_WALKTHROUGH.md'.\n"
        "2. Generate 'project_tracking/SPRINT_REPORT.md'.\n"
        "3. Parse the User Feedback and any outstanding issues.\n"
        "4. Append new Action Items or User Stories to 'project_tracking/backlog.md'.\n"
    )

    pm_agent = agent_factory(
        name="ProductManager",
        instruction=pm_full_instruction,
        tools=worker_tools,
        agent_role="PM"  # Use Flash model for quality requirements
    )
    
    await session_service.create_session(
        app_name="SprintRunner", 
        user_id="user", 
        session_id="retro_session"
    )
    runner = Runner(
        app_name="SprintRunner", 
        agent=pm_agent, 
        session_service=session_service
    )
    
    @retry_decorator
    async def run_retro():
        async for event in runner.run_async(
            user_id="user", 
            session_id="retro_session", 
            new_message=types.Content(parts=[types.Part(text="Conduct Retrospective.")])
        ):
             pass

    await run_retro()
    log("    Retrospective complete. Reports generated and Backlog updated.")

# --- Lifecycle Runner ---
class SprintRunner:
    def __init__(self, agent_factory=default_agent_factory, input_callback=None):
        self.agent_factory = agent_factory
        self.input_callback = input_callback
        self.session_service = InMemorySessionService()

    async def run_cycle(self):
        SprintConfig.validate()
        
        sprint_dir = SprintConfig.get_sprint_dir()
        latest_sprint = detect_latest_sprint_file(sprint_dir)
        if not latest_sprint:
            log(f"No sprint files found in {sprint_dir}")
            return
        
        log(f"[*] Starting Sprint Runner for {latest_sprint}")
        
        # Load shared framework instructions
        framework_index_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_framework_index.md")
        framework_instruction = ""
        if os.path.exists(framework_index_path):
            with open(framework_index_path, "r", encoding="utf-8") as f:
                framework_instruction = f.read()

        # == Execution Loop (Exec -> QA -> Defect -> Exec) ==
        loop_count = 0
        max_loops = 3 # Prevent infinite defect loops
        
        while loop_count < max_loops:
            loop_count += 1
            log(f"\n=== SPRINT CYCLE {loop_count} ===")
            
            # 1. Execute Pending
            tasks_run = await run_parallel_execution(
                self.session_service, framework_instruction, latest_sprint, self.agent_factory
            )
            
            # 2. QA
            defects_found = await run_qa_phase(
                self.session_service, framework_instruction, latest_sprint, self.agent_factory
            )
            
            if defects_found:
                log("    [!] Defects found. Rerunning execution phase for new tasks...")
                continue
            else:
                if tasks_run == 0 and loop_count > 1:
                    break
                    
                if defects_found is False:
                     log("    [+] QA passed. Proceeding to Demo.")
                     break
                
        if loop_count >= max_loops:
            log("WARNING: Max sprint cycles reached. Proceeding to Retro despite potential issues.")

        # 3. Demo
        feedback = await run_demo_phase(
            self.session_service, framework_instruction, latest_sprint, self.agent_factory, self.input_callback
        )
        
        # 4. Retro
        await run_retro_phase(
            self.session_service, framework_instruction, latest_sprint, feedback, self.agent_factory
        )
        
        log("\n[*] Mission execution complete.")

# --- Main Entry Point ---
async def main(project_root=None):
    # Set project root if provided, otherwise default to CWD
    if project_root:
        SprintConfig.set_project_root(project_root)
    else:
        SprintConfig.set_project_root(os.getcwd())
    
    log(f"Project root: {SprintConfig.PROJECT_ROOT}")
    log(f"Sprint directory: {SprintConfig.get_sprint_dir()}")
    
    runner = SprintRunner()
    try:
        await runner.run_cycle()
    except asyncio.CancelledError:
        log("Execution cancelled.")
    except Exception as e:
        log(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Assuming SessionService has a close method, or we rely on context managers.
        # But SessionService instance is created in __init__.
        # We should try to close it if possible.
        # Looking at imported libs, SessionService likely uses a client.
        # If no explicit close, we just ensure we catch the cancel.
        pass



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI Sprint Runner")
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Project root directory (defaults to current working directory)"
    )
    args = parser.parse_args()
    
    try:
        asyncio.run(main(project_root=args.project_root))
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
