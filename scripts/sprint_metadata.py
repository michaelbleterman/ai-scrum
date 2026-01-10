# Helper functions for task metadata management

import os
import re

def parse_task_metadata(task_desc: str, key: str, default=None):
    """
    Parse metadata from task description.
    Format: [POINTS:8|TURNS_ESTIMATED:60|TURNS_USED:47]
    
    Args:
        task_desc: Task description with optional metadata
        key: Metadata key to extract (e.g., "POINTS", "TURNS_ESTIMATED")
        default: Default value if not found
    
    Returns:
        Parsed value or default
    """
    pattern = r'\[([^\]]+)\]'
    match = re.search(pattern, task_desc)
    
    if match:
        metadata_str = match.group(1)
        for pair in metadata_str.split('|'):
            if ':' in pair:
                k, v = pair.split(':', 1)
                if k.strip().upper() == key.upper():
                    # Try to convert to int if possible
                    try:
                        return int(v.strip())
                    except ValueError:
                        return v.strip()
    
    return default


def update_task_metadata_in_file(sprint_file: str, task_desc: str, new_metadata: dict) -> bool:
    """
    Update task metadata in sprint file.
    
    Args:
        sprint_file: Path to sprint markdown file
        task_desc: Task description to find (partial match)
        new_metadata: Dict of metadata to add/update {key: value}
    
    Returns:
        True if updated successfully
    """
    if not os.path.exists(sprint_file):
        return False
    
    with open(sprint_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find task line - match first 30 chars to avoid metadata in search
    # Find task line - match first 30 chars to avoid metadata in search
    task_search = re.escape(task_desc[:50])
    
    # Regex explanation:
    # 1. Start of line (whitespace optional) + bullet + status: ^\s*-\s*\[[x /!]\].*?
    # 2. The task text containing our search term
    # 3. Optional existing metadata at end of line
    # 4. End of line
    pattern = rf'(^\s*-\s*\[[x /!]\]\s*)(.*?{task_search}.*?)(\s*\[.*?\])?(\s*)$'
    
    def replace_metadata(match):
        prefix = match.group(1)  # - [x] 
        task_text = match.group(2)  # Task description
        existing_metadata = match.group(3) or ''  # [POINTS:8|...]
        line_end = match.group(4)  # Whitespace/Newline
        
        # Parse existing metadata
        metadata_dict = {}
        if existing_metadata:
            metadata_str = existing_metadata.strip().strip('[]')
            for pair in metadata_str.split('|'):
                if ':' in pair:
                    k, v = pair.split(':', 1)
                    metadata_dict[k.strip()] = v.strip()
        
        # Update with new metadata
        metadata_dict.update({k: str(v) for k, v in new_metadata.items()})
        
        # Rebuild metadata string
        metadata_pairs = [f"{k}:{v}" for k, v in metadata_dict.items()]
        new_metadata_str = f" [{('|'.join(metadata_pairs))}]" if metadata_pairs else ''
        
        # Remove existing metadata from task_text if present (double cleanup)
        task_text = re.sub(r'\s*\[.*?\]\s*$', '', task_text).strip()
        
        return f"{prefix}{task_text}{new_metadata_str}{line_end}"
    
    updated_content = re.sub(pattern, replace_metadata, content, flags=re.MULTILINE)
    
    if updated_content != content:
        with open(sprint_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    
    return False
