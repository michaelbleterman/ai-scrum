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
from sprint_tools import (
    worker_tools, 
    orchestrator_tools, 
    qa_tools, 
    pm_tools,
    record_turn_usage, 
    update_sprint_task_status, 
    update_sprint_task_status, 
    update_sprint_header,
    search_memory,
    search_memory,
    save_learning,
    send_message,
    receive_messages
)
from sprint_memory import SprintMemoryBank
from sprint_guardrails import AgentGuardrails
from sprint_profile import ProfileManager
from sprint_messaging import MessagingManager
from sprint_utils import detect_latest_sprint_file, parse_sprint_tasks, get_all_sprint_tasks, analyze_sprint_status
from sprint_metadata import parse_task_metadata

import logging
from logging.handlers import RotatingFileHandler

# --- Prompt Sanitization ---
def sanitize_prompt_for_adk(prompt_text):
    """
    Sanitize prompt text to prevent ADK template variable substitution errors.
    
    The ADK processes entire instruction strings and tries to substitute {variable_name} 
    patterns using str.isidentifier(). This function injects a Zero Width Space (\u200b)
    into curly-brace patterns within code blocks to make them invalid identifiers,
    causing the ADK to ignore them while remainining invisible to the LLM.
    
    Args:
        prompt_text: Raw prompt text loaded from markdown files
        
    Returns:
        Sanitized prompt text with "poisoned" identifiers in code blocks
    """
    if not prompt_text:
        return prompt_text
    
    # Pattern to match code blocks (triple backticks)
    code_block_pattern = r'```[\s\S]*?```'
    
    def poison_identifiers(match):
        """Inject zero-width space into {identifier} patterns"""
        content = match.group(0)
        # Find anything that looks like {var} or {var.attr} or {var[key]}
        # and inject \u200b after the first character of the potential identifier
        def replacer(m):
            braces = m.group(1) # { or {{ or {{{
            identifier = m.group(2) # the actual name
            rest = m.group(3) # } or }} or }}}
            if identifier and identifier[0].isalpha():
                return f"{braces}{identifier[0]}\u200b{identifier[1:]}{rest}"
            return m.group(0)

        # Regex to find {identifier} patterns
        # Group 1: Opening braces
        # Group 2: Potential identifier start (alpha + alnum/dot/underscore/bracket)
        # Group 3: Closing braces
        sanitized_content = re.sub(r'(\{+)([a-zA-Z][a-zA-Z0-9_\.\[\]\"\'\-]*)(\}+)', replacer, content)
        return sanitized_content
    
    # Apply poisoning only to code blocks
    sanitized = re.sub(code_block_pattern, poison_identifiers, prompt_text)
    
    return sanitized

# --- Logging Setup ---
def setup_logging(project_root=None):
    """
    Set up logging with project-specific timestamped log files.
    
    Args:
        project_root: Optional project root directory. If provided, logs will be 
                     created in project_root/project_tracking/logs/ with timestamps.
                     Otherwise, falls back to centralized .agent/logs/
    """
    from datetime import datetime
    
    # Determine log directory based on project_root
    if project_root and os.path.exists(project_root):
        # Create logs in project's project_tracking directory
        tracking_dir = os.path.join(project_root, "project_tracking")
        log_dir = os.path.join(tracking_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate timestamped log filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = os.path.basename(project_root)
        log_filename = f"sprint_{project_name}_{timestamp}.log"
        log_file = os.path.join(log_dir, log_filename)
    else:
        # Fallback to centralized logs
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "sprint_debug.log")
    
    # Create file handler (no rotation for timestamped logs, rotation for centralized)
    if project_root:
        # Standard file handler for project-specific logs (each run = new file)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
    else:
        # Rotating handler for centralized logs
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
    
    # Log the log file location
    logger.info(f"Logging to: {log_file}")
    
    return logger

# Logger will be initialized with project context in main()
logger = None

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

def validate_sprint_state(sprint_file):
    """
    Validates if a sprint is ready to run or needs planning.
    
    Returns:
        'ready': Sprint has tasks and can be executed
        'needs_planning': Sprint exists but has no tasks
        'completed': All tasks are done
    """
    status = analyze_sprint_status(sprint_file)
    
    # Check if sprint has any tasks defined
    if status['total'] == 0:
        return 'needs_planning'
    
    # Check if sprint is completed (all tasks done, none in other states)
    if status.get('done', 0) == status['total'] and status['total'] > 0:
        # Double-check no pending/in-progress/blocked tasks
        if status.get('todo', 0) == 0 and status.get('in_progress', 0) == 0 and status.get('blocked', 0) == 0:
            return 'completed'
    
    return 'ready'

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
async def run_parallel_execution(
    session_service, 
    framework_instruction, 
    sprint_file, 
    agent_factory=default_agent_factory, 
    memory_bank=None, 
    guardrails=None, 
    profile_manager=None,
    messaging_manager=None
):
    log("\n[Phase 1] Parallel Execution: Analyzing sprint status...")
    await update_sprint_header("In Progress", SprintConfig.get_sprint_dir())
    
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
    role_map = SprintConfig.get_role_map()
    
    # Track retry attempts per task description to prevent infinite blocked loops
    task_retry_tracker = {}
    MAX_BLOCKED_RETRIES = 2
    
    # Create a Queue and populate it
    queue = asyncio.Queue()
    for idx, task in enumerate(tasks_to_execute):
        await queue.put((idx, task))
        
    async def worker(worker_id):
        while True:
            try:
                # Get a "unit of work" from the queue.
                task_index, task_info = await queue.get()
                
                try:
                    role_raw = task_info["role"]
                    role = role_raw.lower()
                    desc = task_info["desc"]
                    status = task_info["status"]
                    blocker_reason = task_info.get("blocker_reason")
                    
                    # --- Inject Messaging Context ---
                    if messaging_manager:
                        send_message._messaging_manager = messaging_manager
                        receive_messages._messaging_manager = messaging_manager
                        send_message._agent_role = role_raw
                        receive_messages._agent_role = role_raw
                    
                    if guardrails:
                        # --- Guardrails Input Validation ---
                        is_valid, violations = guardrails.validate_input(desc)
                        if not is_valid:
                            log(f"\n    [Worker {worker_id} -> Task {task_index+1}] BLOCKED by guardrails:")
                            for v in violations:
                                log(f"      - {v.reason}")
                            
                            await update_sprint_task_status(
                                desc, "[!]",
                                blocker_reason=f"Guardrail violation: {violations[0].reason}",
                                sprint_dir=SprintConfig.get_sprint_dir()
                            )
                            queue.task_done()
                            continue

                        # --- Circuit Breaker Check ---
                        allowed, circuit_reason = guardrails.check_circuit(desc)
                        if not allowed:
                            log(f"\n    [Worker {worker_id} -> Task {task_index+1}] Circuit breaker OPEN: {circuit_reason}")
                            await update_sprint_task_status(
                                desc, "[!]",
                                blocker_reason=circuit_reason,
                                sprint_dir=SprintConfig.get_sprint_dir()
                            )
                            queue.task_done()
                            continue
                    
                    # Check retry limit for blocked tasks
                    if status == "blocked":
                        retry_count = task_retry_tracker.get(desc, 0)
                        if retry_count >= MAX_BLOCKED_RETRIES:
                            log(f"\n    [Worker {worker_id} -> Task {task_index+1}] SKIPPING - exceeded retry limit ({retry_count} attempts): @{role_raw}: {desc}")
                            log(f"    This task requires manual intervention. Check logs for previous failure reasons.")
                            queue.task_done()
                            continue
                        else:
                            log(f"\n    [Worker {worker_id} -> Task {task_index+1}] Retrying blocked task (attempt {retry_count + 1}/{MAX_BLOCKED_RETRIES}): @{role_raw}: {desc}")
                    
                    status_label = status.upper().replace('_', '-')
                    log(f"\n    [Worker {worker_id} -> Task {task_index+1}] Starting @{role_raw} [{status_label}]: {desc}")
                    
                    # DIRECT UPDATE: Mark in-progress
                    try:
                        await update_sprint_task_status(desc, "[/]", SprintConfig.get_sprint_dir())
                    except Exception as e:
                        log(f"    [Update Error] Failed to mark in-progress: {e}")

                    prompt_file = role_map.get(role_raw, "agent_orchestrator.md")
                    prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, prompt_file)
                    if os.path.exists(prompt_path):
                        with open(prompt_path, "r", encoding="utf-8") as f:
                            instruction = sanitize_prompt_for_adk(f.read())
                    else:
                        instruction = f"Act as {role}."

                    agent_name = f"{re.sub(r'[^a-zA-Z0-9_]', '', role)}_{task_index}"
                    
                    
                    # Discover and inject project context (cached per execution)
                    if not hasattr(run_parallel_execution, '_project_context_cache'):
                        try:
                            from sprint_tools import discover_project_context
                            project_root = SprintConfig.PROJECT_ROOT or os.getcwd()
                            context_json = discover_project_context(project_root)
                            run_parallel_execution._project_context_cache = context_json
                            log(f"    [Context Discovery] Discovered project context: {context_json[:200]}...")
                        except Exception as e:
                            run_parallel_execution._project_context_cache = '{"error": "Context discovery failed"}'
                            log(f"    [Context Discovery] Failed: {e}")
                    
                    project_context_instruction = (
                        f"\n\n=== PROJECT CONTEXT ===\n"
                        f"Working Directory: {SprintConfig.PROJECT_ROOT or os.getcwd()}\n"
                        f"Technology Stack Analysis:\n{run_parallel_execution._project_context_cache}\n"
                        f"\n**CRITICAL**: You MUST use the technologies listed above. "
                        f"Do NOT introduce new languages or frameworks.\n"
                        f"========================\n"
                    )
                    
                    # --- Profiling: Load and Inject Profile ---
                    profile_context = ""
                    if profile_manager:
                         profile = profile_manager.get_profile(name=role_raw, role=role_raw)
                         profile_context = f"\n\n=== AGENT PROFILE ===\n"
                         profile_context += f"Identity: {profile.name} (Level {profile.level} {profile.role})\n"
                         profile_context += f"XP: {profile.total_xp} | Success Rate: {profile.stats.get('success_rate', 0)}%\n"
                         if profile.skills:
                             profile_context += f"Skills: {', '.join(profile.skills)}\n"

                    # --- Memory Recall ---
                    memory_context = ""
                    if memory_bank and memory_bank.enable_memory:
                        try:
                            relevant_memories = memory_bank.recall(query=desc, top_k=3)
                            if relevant_memories:
                                log(f"    [Task {task_index+1}] Found {len(relevant_memories)} relevant memories")
                                memory_context = "\n\n=== RELEVANT PAST EXPERIENCES (MEMORY BANK) ===\n"
                                memory_context += "Use these insights to guide your implementation and avoid past errors:\n"
                                for i, mem in enumerate(relevant_memories, 1):
                                    relevance = 1 - mem.get('distance', 1.0)
                                    mem_type = mem.get('metadata', {}).get('memory_type', 'unknown')
                                    memory_context += f"{i}. [{relevance:.0%} relevant] ({mem_type}) {mem['content']}\n"
                                memory_context += "===============================================\n"
                        except Exception as mem_err:
                            log(f"    [Memory Recall] Failed: {mem_err}")
                    
                    full_instruction = f"{framework_instruction}\n\n{instruction}\n{profile_context}\n{project_context_instruction}\n{memory_context}\n\nTask: {desc}"
                    
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
                        # Initialize budget from metadata if available, else default
                        initial_budget = parse_task_metadata(desc, 'TURNS_ESTIMATED', default=40)
                        soft_limit = max(40, initial_budget)
                        hard_limit = soft_limit * 2  # Progressive limit: 2x safety buffer
                        log(f"    [Agent {role_raw}] Starting with soft limit: {soft_limit}, hard limit: {hard_limit}")
                        
                        async for event in runner.run_async(
                            user_id="user", 
                            session_id=worker_pid, 
                            new_message=types.Content(parts=[types.Part(text=f"Execute this task: {desc}")])
                        ):
                            turn_count += 1
                            
                            # Check for budget updates from tool calls
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
                                        
                                        # Dynamic Budget Update
                                        if part.function_call.name == "request_turn_budget":
                                            try:
                                                # args is a dict or struct, need to parse
                                                args = part.function_call.args
                                                if isinstance(args, dict):
                                                    est = args.get('estimated_turns', 20)
                                                else:
                                                    # Handle proto Struct conversion if needed
                                                    est = args['estimated_turns']
                                                
                                                # Progressive limits: soft = estimate, hard = 2x
                                                soft_limit = max(20, int(est))
                                                hard_limit = soft_limit * 2
                                                log(f"    [Agent {role_raw}] Budget UPDATED - Soft: {soft_limit}, Hard: {hard_limit}")
                                            except Exception as ex:
                                                logger.error(f"Failed to parse turn budget update: {ex}")

                            # Progressive limit enforcement
                            if turn_count > soft_limit and turn_count <= hard_limit:
                                overage = turn_count - soft_limit
                                remaining = hard_limit - turn_count
                                msg = f"[Agent {role_raw}] ⚠️  WARNING: Exceeded estimate by {overage} turns, {remaining} turns until hard limit"
                                logger.warning(msg)
                                print(msg)
                            
                            if turn_count > hard_limit:
                                msg = f"[Agent {role_raw}] ❌ EXCEEDED HARD LIMIT ({hard_limit}). Killing."
                                logger.error(msg)
                                print(msg) # Print to stdout for test capture
                                raise RuntimeError(f"Task exceeded hard limit ({hard_limit})")

                        return turn_count

                    try:
                        actual_turns = await run_agent()
                        log(f"    [Task {task_index+1}] Completed @{role_raw} in {actual_turns} turns")
                        
                        # Record actual usage
                        record_turn_usage(desc, actual_turns)
                        
                        # Record success for circuit breaker
                        if guardrails:
                            guardrails.record_action(desc, success=True)
                            
                        # Update Profile (XP)
                        if profile_manager:
                            points = 10 # Default base XP
                            if "POINTS:" in desc:
                                try:
                                    points = int(desc.split("POINTS:")[1].split("|")[0].split("]")[0]) * 10
                                except:
                                    pass
                            profile_manager.update_profile(role_raw, xp_gain=points, success=True, turns=actual_turns)
                        
                        # DIRECT UPDATE: Mark done
                        await update_sprint_task_status(desc, "[x]", SprintConfig.get_sprint_dir())
                        
                        # Store success in memory
                        if memory_bank and memory_bank.enable_memory:
                            try:
                                memory_bank.store(
                                    content=f"Task '{desc}' completed successfully by {role_raw}",
                                    memory_type="task_outcome",
                                    metadata={
                                        "role": role_raw,
                                        "turns": actual_turns,
                                        "status": "success",
                                        "sprint_file": sprint_file
                                    }
                                )
                            except Exception as mem_e:
                                log(f"    [Memory Store] Failed to store success: {mem_e}")

                    except Exception as e:
                        log(f"    [Task {task_index+1}] FAILED @{role_raw}: {e}")
                        
                        # Record failure for circuit breaker
                        if guardrails:
                            guardrails.record_action(desc, success=False)
                            
                        # Update Profile (Failure)
                        if profile_manager:
                            profile_manager.update_profile(role_raw, xp_gain=1, success=False, turns=actual_turns)
                        
                        # Store failure in memory
                        if memory_bank and memory_bank.enable_memory:
                            try:
                                memory_bank.store(
                                    content=f"Task '{desc}' failed: {str(e)}",
                                    memory_type="error_resolution",
                                    metadata={
                                        "role": role_raw,
                                        "error": str(e),
                                        "status": "failed",
                                        "sprint_file": sprint_file
                                    }
                                )
                            except Exception as mem_e:
                                log(f"    [Memory Store] Failed to store error: {mem_e}")
                        # Record partial usage (best effort)
                        # Note: We can't easily get partial turn count here as it's local to run_agent
                        # Unless run_agent returns it in exception or we track it externally.
                        # For now, we skip partial recording on failure or implement retry logic
                        
                        # Track failure for retry limit
                        task_retry_tracker[desc] = task_retry_tracker.get(desc, 0) + 1
                        # Mark as blocked if it fails
                        await update_sprint_task_status(desc, "[!]", SprintConfig.get_sprint_dir())
                
                finally:
                    # Notify the queue that the "unit of work" is complete
                    queue.task_done()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                log(f"Worker {worker_id} crashed: {e}")
                # Don't let a worker crash kill the whole thing, unless we want it to.
                # But we should probably restart it or just let it die if we have others.
                # For now, just log and continue loop unless it's critical.
                # If we used queue.task_done() inside the inner try/finally, we are good.
                pass

    # Start workers
    workers = []
    for i in range(concurrency_limit):
        w = asyncio.create_task(worker(i))
        workers.append(w)

    # Wait until the queue is fully processed
    await queue.join()

    # Cancel our worker tasks
    for w in workers:
        w.cancel()
    
    # Wait until all worker tasks are cancelled
    await asyncio.gather(*workers, return_exceptions=True)
    
    return len(tasks_to_execute)

# --- Phase 2: QA & Validation ---
async def run_qa_phase(session_service, framework_instruction, sprint_file, agent_factory=default_agent_factory):
    log("\n[Phase 2] QA Verification: Validating completed tasks...")
    await update_sprint_header("QA", SprintConfig.get_sprint_dir())
    
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
             qa_instruction = sanitize_prompt_for_adk(f.read())
    else:
        qa_instruction = "You are the QA Engineer."

    qa_full_instruction = (
        f"{framework_instruction}\n\n{qa_instruction}\n\n"
        f"Tasks to Verify:\n{task_list_str}\n\n"
        "Execute the QA workflow defined in your agent prompt for the above tasks."
    )

    # Load DevOps QA Setup prompt
    devops_qa_setup_prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_devops.md")  # Consolidated QA setup in main DevOps prompt
    if os.path.exists(devops_qa_setup_prompt_path):
        with open(devops_qa_setup_prompt_path, "r", encoding="utf-8") as f:
            devops_setup_instruction = sanitize_prompt_for_adk(f.read())
    else:
        devops_setup_instruction = "Prepare the test environment for QA execution."

    devops_full_instruction = f"{framework_instruction}\n\n{devops_setup_instruction}"

    devops_agent = agent_factory(
        name="DevOps_Setup",
        instruction=devops_full_instruction,
        tools=worker_tools,
        agent_role="DevOps"
    )

    devops_pid = f"devops_setup_{os.urandom(4).hex()}"
    await session_service.create_session(
        app_name="SprintRunner", 
        user_id="user", 
        session_id=devops_pid
    )
    devops_runner = Runner(
        app_name="SprintRunner", 
        agent=devops_agent, 
        session_service=session_service
    )

    @retry_decorator
    async def run_devops_setup():
        turn_count = 0
        max_turns = 40  # Reverted: progressive limits handle buffers
        async for event in devops_runner.run_async(
            user_id="user", 
            session_id=devops_pid, 
            new_message=types.Content(parts=[types.Part(text="Setup environment for QA.")])
        ):
            turn_count += 1
            if turn_count > max_turns:
                 log(f"[DevOps] EXCEEDED MAX TURNS ({max_turns}). Stopping setup.")
                 raise RuntimeError(f"DevOps setup exceeded max turns ({max_turns})")
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        logger.info(f"[DevOps] Thought: {part.text}")
                    if getattr(part, 'function_call', None):
                        logger.info(f"[DevOps] Call: {part.function_call.name}({part.function_call.args})")

    await run_devops_setup()
    log("    [QA Phase] Environment Setup Complete. Starting QA Agent...")
    # ----------------------------------------

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
        turn_count = 0
        max_turns = 100  # Increased from 40 to handle complex QA scenarios
        async for event in runner.run_async(
            user_id="user", 
            session_id=qa_pid, 
            new_message=types.Content(parts=[types.Part(text="Begin QA verification.")])
        ):
            turn_count += 1
            if turn_count > max_turns:
                 log(f"[QA] EXCEEDED MAX TURNS ({max_turns}). Stopping.")
                 raise RuntimeError(f"QA verification exceeded max turns ({max_turns})")
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
    
    # Load Demo Orchestrator prompt
    demo_prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_orchestrator_demo.md")
    if os.path.exists(demo_prompt_path):
        with open(demo_prompt_path, "r", encoding="utf-8") as f:
            demo_instruction = sanitize_prompt_for_adk(f.read())
    else:
        demo_instruction = "Prepare a Demo Walkthrough."

    orchestrator_full_instruction = f"{framework_instruction}\n\n{demo_instruction}"
    
    orchestrator_agent = agent_factory(
        name="Orchestrator",
        instruction=orchestrator_full_instruction,
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
        turn_count = 0
        max_turns = 20
        async for event in runner.run_async(
            user_id="user", 
            session_id="demo_session", 
            new_message=types.Content(parts=[types.Part(text="Create the demo walkthrough.")])
        ):
            turn_count += 1
            if turn_count > max_turns:
                 log(f"[Orchestrator] EXCEEDED MAX TURNS ({max_turns}). Stopping.")
                 raise RuntimeError(f"Demo walkthrough generation exceeded max turns ({max_turns})")
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
        # Default to non-interactive if NO TTY or Env var set
        is_interactive = sys.stdin.isatty() and not os.environ.get("NON_INTERACTIVE")
        
        if not is_interactive:
            feedback = "No feedback provided (Non-interactive mode)."
            log("    [Info] Non-interactive mode detected. Skipping user input.")
        else:
            try:
                print("    >> Please enter your feedback for this sprint (or press Enter to skip):")
                feedback = input("    Feedback: > ")
            except EOFError:
                feedback = "No feedback provided (EOF)."
        
    return feedback

# --- Phase 4: Retro ---
async def run_retro_phase(session_service, framework_instruction, sprint_file, demo_feedback, agent_factory=default_agent_factory):
    log("\n[Phase 4] Retrospective")
    await update_sprint_header("Review", SprintConfig.get_sprint_dir())
    
    # Load PM Retrospective prompt
    retro_prompt_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_pm_retrospective.md")
    if os.path.exists(retro_prompt_path):
        with open(retro_prompt_path, "r", encoding="utf-8") as f:
            pm_retro_instruction = sanitize_prompt_for_adk(f.read())
            # Inject user feedback into the template
            user_feedback_text = demo_feedback if demo_feedback else "None provided."
            pm_retro_instruction = pm_retro_instruction.replace("{user_feedback}", user_feedback_text)
    else:
        pm_retro_instruction = "Conduct sprint retrospective."

    pm_full_instruction = f"{framework_instruction}\n\n{pm_retro_instruction}"

    pm_agent = agent_factory(
        name="ProductManager",
        instruction=pm_full_instruction,
        tools=pm_tools,
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
        turn_count = 0
        max_turns = 40
        async for event in runner.run_async(
            user_id="user", 
            session_id="retro_session", 
            new_message=types.Content(parts=[types.Part(text="Conduct Retrospective.")])
        ):
            turn_count += 1
            if turn_count > max_turns:
                 log(f"[PM] EXCEEDED MAX TURNS ({max_turns}). Stopping.")
                 raise RuntimeError(f"Retrospective exceeded max turns ({max_turns})")
             
    await run_retro()
    log("    Retrospective complete. Reports generated and Backlog updated.")

# --- Lifecycle Runner ---
class SprintRunner:
    def __init__(self, agent_factory=default_agent_factory, input_callback=None, memory_bank=None, messaging_manager=None):
        self.agent_factory = agent_factory
        self.input_callback = input_callback
        self.session_service = InMemorySessionService()
        self.memory_bank = memory_bank
        self.messaging_manager = messaging_manager
        
        # Initialize guardrails
        self.guardrails = AgentGuardrails(
            denied_topics=['password', 'api_key', 'secret', 'token'],
            enable_pii_detection=True, # os.getenv("ENABLE_GUARDRAILS", "true") == "true"
            enable_content_filter=True,
            enable_circuit_breaker=True
        )
        
        # Initialize Profiling
        self.profile_manager = ProfileManager(SprintConfig.get_sprint_dir())

    async def run_cycle(self):
        SprintConfig.validate()
        
        sprint_dir = SprintConfig.get_sprint_dir()
        latest_sprint = detect_latest_sprint_file(sprint_dir)
        if not latest_sprint:
            log(f"No sprint files found in {sprint_dir}")
            return
        
        log(f"[*] Starting Sprint Runner for {latest_sprint}")
        
        # Validate sprint state before execution
        sprint_state = validate_sprint_state(latest_sprint)
        log(f"Sprint state: {sprint_state}")
        
        if sprint_state == 'completed':
            log(f"✅ Sprint {latest_sprint} is already completed!")
            log(f"All tasks are done. Start a new sprint or run retrospective.")
            return
        elif sprint_state == 'needs_planning':
            log(f"⚠️  Sprint {latest_sprint} has no tasks defined.")
            log(f"This sprint needs to be populated by the PM agent before execution.")
            return
        
        # Load shared framework instructions
        framework_index_path = os.path.join(SprintConfig.PROMPT_BASE_DIR, "agent_framework_index.md")
        framework_instruction = ""
        if os.path.exists(framework_index_path):
            with open(framework_index_path, "r", encoding="utf-8") as f:
                framework_instruction = sanitize_prompt_for_adk(f.read())

        # == Execution Loop (Exec -> QA -> Defect -> Exec) ==
        loop_count = 0
        max_loops = 3 # Prevent infinite defect loops
        
        while loop_count < max_loops:
            loop_count += 1
            log(f"\n=== SPRINT CYCLE {loop_count} ===")
            
            # 1. Execute Pending
            tasks_run = await run_parallel_execution(
                self.session_service, 
                framework_instruction, 
                latest_sprint, 
                self.agent_factory, 
                memory_bank=self.memory_bank, 
                guardrails=self.guardrails, 
                profile_manager=self.profile_manager,
                messaging_manager=self.messaging_manager
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
    global logger
    
    # Set project root if provided, otherwise default to CWD
    if project_root:
        SprintConfig.set_project_root(project_root)
    else:
        SprintConfig.set_project_root(os.getcwd())
    
    # Initialize logger with project context
    logger = setup_logging(SprintConfig.PROJECT_ROOT)
    
    log(f"Project root: {SprintConfig.PROJECT_ROOT}")
    log(f"Sprint directory: {SprintConfig.get_sprint_dir()}")
    
    # Initialize memory bank
    enable_memory = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
    memory_bank = SprintMemoryBank(SprintConfig.PROJECT_ROOT, enable_memory=enable_memory)
    log(f"Memory Bank: {memory_bank.get_statistics()}")
    
    # Initialize messaging manager
    messaging_manager = MessagingManager(SprintConfig.PROJECT_ROOT)
    
    # Inject memory bank into tools
    search_memory._memory_bank = memory_bank
    save_learning._memory_bank = memory_bank
    
    # Inject messaging manager into tools
    send_message._messaging_manager = messaging_manager
    receive_messages._messaging_manager = messaging_manager
    
    runner = SprintRunner(memory_bank=memory_bank, messaging_manager=messaging_manager)
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
