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

    # Look for the Task Breakdown section
    sections = re.split(r"### ", content)
    for section in sections:
        lines = section.split("\n")
        header = lines[0]
        # Identify roles in the header (e.g., @Backend @Security)
                # Identify roles in the header (e.g., @Backend @Security)
        roles = re.findall(r"@(\w+)", header)
        if not roles:
            # Fallback: try to identify role from "### Backend Tasks"
            header_role = re.search(r"###\s+(\w+)", header)
            if header_role:
                roles = [header_role.group(1)]
            else:
                continue

        for line in lines[1:]:
            # Match todo items: - [ ] Task description OR - [/] Task description (resume)
            # We want to pick up [/] tasks if the runner restarted/crashed.
            match = re.search(r"- \[[ /]\] (.*)", line)
            if match:
                desc = match.group(1).strip()
                # For simplicity, assign to the first role mentioned in the section
                tasks.append({"role": roles[0], "desc": desc})
    
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

    sections = re.split(r"### ", content)
    for section in sections:
        lines = section.split("\n")
        header = lines[0]
        roles = re.findall(r"@(\w+)", header)
        if not roles:
            continue

        for line in lines[1:]:
            # Match strictly tasks with checkboxes
            # regex groups: 1=status_char, 2=description
            match = re.search(r"- \[([ x/!])\] (.*)", line)
            if match:
                status_char = match.group(1)
                desc = match.group(2).strip()
                
                status_map = {
                    " ": "todo",
                    "x": "done",
                    "/": "in_progress",
                    "!": "blocked"
                }
                status = status_map.get(status_char, "unknown")
                
                tasks.append({
                    "role": roles[0], 
                    "desc": desc, 
                    "status": status,
                    "raw_line": line.strip()
                })
    return tasks
