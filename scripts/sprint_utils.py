import os
import re

def detect_latest_sprint_file(sprint_dir: str):
    """Finds the latest SPRINT_*.md file in the given directory."""
    if not os.path.exists(sprint_dir):
        return None
        
    sprint_files = [f for f in os.listdir(sprint_dir) if f.startswith("SPRINT_") and f.endswith(".md")]
    if not sprint_files:
        return None
    
    sprint_files.sort()
    return os.path.join(sprint_dir, sprint_files[-1])

def parse_sprint_tasks(sprint_file_path: str):
    """
    Parses the Task Breakdown section of a sprint markdown file.
    Returns a list of tasks with role and description.
    """
    tasks = []
    if not sprint_file_path or not os.path.exists(sprint_file_path):
        print(f"Error: Sprint file {sprint_file_path} not found.")
        return tasks

    with open(sprint_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for the Task Breakdown section
    # Assuming Task Breakdown is marked with ### or similar. 
    # The original logic split by "### ".
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
            # Also capture in-progress or done tasks if needed, but usually we run what is unchecked [ ]
            # The original script targeted [ ]
            match = re.search(r"- \[ \] (.*)", line)
            if match:
                desc = match.group(1).strip()
                # For simplicity, assign to the first role mentioned in the section
                tasks.append({"role": roles[0], "desc": desc})
    
    return tasks
