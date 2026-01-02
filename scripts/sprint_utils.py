import os
import re

def detect_latest_sprint_file(sprint_dir: str):
    """Finds the latest SPRINT_*.md file in the given directory, excluding reports."""
    if not os.path.exists(sprint_dir):
        return None
        
    sprint_files = [
        f for f in os.listdir(sprint_dir) 
        if f.startswith("SPRINT_") and f.endswith(".md") and "REPORT" not in f
    ]
    if not sprint_files:
        return None
    
    sprint_files.sort()
    return os.path.join(sprint_dir, sprint_files[-1])

def parse_sprint_tasks(sprint_file_path: str):
    """
    Parses the Task Breakdown section of a sprint markdown file.
    Returns a list of tasks with role and description that are pending [ ].
    """
    tasks = []
    if not sprint_file_path or not os.path.exists(sprint_file_path):
        print(f"Error: Sprint file {sprint_file_path} not found.")
        return tasks

    with open(sprint_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by headers (H1-H6) to process sections, but keep it simple for now.
    # We'll just iterate line by line to support mixed formats better.
    lines = content.split("\n")
    
    current_section_roles = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 1. Check for Section Headers with Roles (e.g. "### @Backend Tasks")
        if line_stripped.startswith("#"):
            # Extract roles from header if any
            found_roles = re.findall(r"@(\w+)", line_stripped)
            if found_roles:
                current_section_roles = found_roles
            # Note: We don't clear roles on headers without roles, to allow 
            # "### Sub-section" to inherit from "## @Role Section" if we were that advanced.
            # But for now, let's keep it simple: strict scope or inline.
            # Actually, standardizing: if a header triggers a new context, use it. 
            # If no roles in header, maybe clear it? 
            # For SPRINT_2.md logic (Epic headers have no roles), we rely on inline.
            elif "Epic" in line_stripped or "Story" in line_stripped:
                current_section_roles = [] # Reset for new Epic/Story if no explicit role in header

        # 2. Check for Task Items
        # Matches: - [ ] ... or - [/] ...
        task_match = re.search(r"^\s*-\s*\[([ /])\]\s*(.*)", line)
        if task_match:
            status_char = task_match.group(1)
            full_desc = task_match.group(2).strip()
            
            # Check for inline role: "@DevOps: Do something" or "@Backend Do something"
            # Regex: Start of description, @Role, optional colon, space
            inline_role_match = re.match(r"^@(\w+)[:\s]\s*(.*)", full_desc)
            
            role = None
            desc = full_desc
            
            if inline_role_match:
                role = inline_role_match.group(1)
                desc = inline_role_match.group(2)
            elif current_section_roles:
                role = current_section_roles[0]
            
            if role:
                # We only care about pending ([ ]) or in-progress ([/]) tasks here
                tasks.append({"role": role, "desc": desc})

    return tasks

def get_all_sprint_tasks(sprint_file_path: str):
    """
    Parses ALL tasks from the sprint file, returning their status, role, and description.
    Returns list of dicts: {'role': str, 'desc': str, 'status': str}
    Status can be 'todo' [ ], 'in_progress' [/], 'done' [x], 'blocked' [!], 'defect' [?] or similar.
    """
    tasks = []
    if not sprint_file_path or not os.path.exists(sprint_file_path):
        return tasks

    with open(sprint_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    current_section_roles = []

    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith("#"):
            found_roles = re.findall(r"@(\w+)", line_stripped)
            if found_roles:
                current_section_roles = found_roles
            elif "Epic" in line_stripped or "Story" in line_stripped:
                current_section_roles = []

        # Match any status char inside []
        task_match = re.search(r"^\s*-\s*\[([ x/!?.])\]\s*(.*)", line)
        if task_match:
            status_char = task_match.group(1)
            full_desc = task_match.group(2).strip()
            
            inline_role_match = re.match(r"^@(\w+)[:\s]\s*(.*)", full_desc)
            
            role = None
            desc = full_desc
            
            if inline_role_match:
                role = inline_role_match.group(1)
                desc = inline_role_match.group(2)
            elif current_section_roles:
                role = current_section_roles[0]
            
            if role:
                status_map = {
                    " ": "todo",
                    "x": "done",
                    "/": "in_progress",
                    "!": "blocked",
                    "?": "defect"
                }
                status = status_map.get(status_char, "unknown")
                
                tasks.append({
                    "role": role, 
                    "desc": desc, 
                    "status": status,
                    "raw_line": line_stripped
                })
    return tasks
