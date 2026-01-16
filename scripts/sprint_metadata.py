# Helper functions for task metadata management

import os
import re
import difflib

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
    Update task metadata in sprint file using fuzzy matching.
    
    Args:
        sprint_file: Path to sprint markdown file
        task_desc: Task description to find (partial match)
        new_metadata: Dict of metadata to add/update {key: value}
    
    Returns:
        True if updated successfully
    """
    if not os.path.exists(sprint_file):
        return False
    
    # Read all lines
    try:
        with open(sprint_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return False
    
    # Clean up the input task description for comparison
    # Remove metadata, bullets, extra whitespace, quotes
    clean_search = re.sub(r'\[.*?\]', '', task_desc)
    clean_search = re.sub(r'^[\s\-\*]+', '', clean_search)
    clean_search = re.sub(r'[\'"`]', '', clean_search).strip().lower()
    
    best_ratio = 0.0
    best_idx = -1
    
    # 1. Fuzzy Match Phase
    for i, line in enumerate(lines):
        # Only check lines that look like tasks
        if not re.match(r'^\s*-\s*\[[x /!]\]', line):
            continue
            
        # Clean up the line content
        clean_line = re.sub(r'\[.*?\]', '', line) # remove existing metadata
        clean_line = re.sub(r'^\s*-\s*\[[x /!]\]', '', clean_line) # remove checkmark
        clean_line = re.sub(r'[\'"`]', '', clean_line).strip().lower()
        
        # Calculate similarity
        ratio = difflib.SequenceMatcher(None, clean_search, clean_line).ratio()
        
        # Boost ratio if one is substring of other
        if clean_search in clean_line or clean_line in clean_search:
            ratio = max(ratio, 0.85)

        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = i
            
    # Threshold for match acceptance (0.6 is loose but safe given context)
    if best_ratio < 0.6:
        return False
        
    # 2. Update Phase
    target_line = lines[best_idx]
    
    # Extract parts: Prefix, Content, Metadata, Suffix
    # Regex: (Prefix)(Content)(Metadata?)(Whitespace)
    match = re.match(r'(^\s*-\s*\[[x /!]\]\s*)(.*?)(\s*\[.*?\])?(\s*)$', target_line)
    
    if not match:
        # Fallback if regex fails on the specific line (unlikely given check above)
        return False
        
    prefix = match.group(1)
    task_text = match.group(2)
    existing_metadata = match.group(3) or ''
    line_end = match.group(4).strip('\n') # keep mostly just newline at end logic handled below explicitly
    
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
    
    # Remove existing metadata from task_text if present in group 2 (double cleanup)
    task_text = re.sub(r'\s*\[.*?\]\s*$', '', task_text).strip()
    
    # Construct new line
    new_line = f"{prefix}{task_text}{new_metadata_str}\n"
    
    if new_line != target_line:
        lines[best_idx] = new_line
        with open(sprint_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    
    # Even if content didn't change, we found the task, so return True
    return True


def update_task_status_in_file(sprint_file: str, task_desc: str, status: str) -> bool:
    """
    Update task status in sprint file using fuzzy matching.
    
    Args:
        sprint_file: Path to sprint markdown file
        task_desc: Task description to find (partial match)
        status: New status string (e.g. "[x]", "[/]")
    
    Returns:
        True if updated successfully
    """
    if not os.path.exists(sprint_file):
        return False
    
    try:
        with open(sprint_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return False
    
    # Clean up the input task description for comparison
    clean_search = re.sub(r'\[.*?\]', '', task_desc)
    clean_search = re.sub(r'^[\s\-\*]+', '', clean_search)
    clean_search = re.sub(r'[\'"`]', '', clean_search).strip().lower()
    
    best_ratio = 0.0
    best_idx = -1
    
    # 1. Fuzzy Match Phase
    for i, line in enumerate(lines):
        # Only check lines that look like tasks
        if not re.match(r'^\s*-\s*\[[x /!]\]', line):
            continue
            
        # Clean up the line content
        clean_line = re.sub(r'\[.*?\]', '', line)
        clean_line = re.sub(r'^\s*-\s*\[[x /!]\]', '', clean_line)
        clean_line = re.sub(r'[\'"`]', '', clean_line).strip().lower()
        
        ratio = difflib.SequenceMatcher(None, clean_search, clean_line).ratio()
        
        if clean_search in clean_line or clean_line in clean_search:
            ratio = max(ratio, 0.85)

        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = i
            
    if best_ratio < 0.6:
        return False
        
    # 2. Update Phase
    target_line = lines[best_idx]
    
    # Regex to replace status checkbox
    # - [ ] or - [x] or - [/]
    new_line = re.sub(r'(-\s*\[)[x /!](\])', fr'\1{status.strip("[]")}\2', target_line, count=1)
    
    if new_line != target_line:
        lines[best_idx] = new_line
        with open(sprint_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    
    return True
