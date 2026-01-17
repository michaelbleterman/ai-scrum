"""
Agent-to-agent messaging system for sprint framework.
Enables parallel agents to collaborate, share context, and notify dependencies.
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Try to import msvcrt for Windows file locking
try:
    import msvcrt
except ImportError:
    msvcrt = None

@dataclass
class Message:
    """Structure for agent messages"""
    sender: str
    recipient: str  # Can be 'all' for broadcast
    content: str
    message_type: str  # 'info', 'request', 'notification', 'dependency'
    timestamp: str = ""
    message_id: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.message_id:
            self.message_id = f"msg_{int(time.time() * 1000)}_{os.urandom(4).hex()}"

class MessagingManager:
    """
    Manages a file-based message bus with locking for concurrent access.
    """
    
    def __init__(self, project_root: str, messaging_file: str = "messages.json"):
        self.project_root = Path(project_root).resolve()
        self.messaging_dir = self.project_root / "project_tracking"
        self.messaging_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.messaging_dir / messaging_file
        
        # Initialize file if not exists
        if not self.file_path.exists():
            self._write_messages([])

    def _lock_file(self, f):
        if msvcrt:
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_file(self, f):
        if msvcrt:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except:
                pass

    def _read_messages(self) -> List[Dict]:
        """Read all messages with locking"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self._lock_file(f)
                try:
                    content = f.read()
                    if not content:
                        return []
                    return json.loads(content)
                finally:
                    self._unlock_file(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _write_messages(self, messages: List[Dict]):
        """Write all messages with locking"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            self._lock_file(f)
            try:
                json.dump(messages, f, indent=2)
            finally:
                self._unlock_file(f)

    def send_message(self, sender: str, recipient: str, content: str, message_type: str = "info") -> str:
        """Send a new message"""
        msg = Message(sender=sender, recipient=recipient, content=content, message_type=message_type)
        
        # Use r+ to read and write atomically
        try:
            with open(self.file_path, "r+", encoding="utf-8") as f:
                self._lock_file(f)
                try:
                    current_content = f.read()
                    messages = json.loads(current_content) if current_content else []
                    messages.append(asdict(msg))
                    f.seek(0)
                    json.dump(messages, f, indent=2)
                    f.truncate()
                finally:
                    self._unlock_file(f)
        except FileNotFoundError:
            self._write_messages([asdict(msg)])
            
        return msg.message_id

    def get_messages(self, recipient: str, since_id: Optional[str] = None) -> List[Dict]:
        """
        Get messages for a specific recipient (including broadcast messages).
        """
        all_messages = self._read_messages()
        
        # Filter by recipient
        recipient_lower = recipient.lower()
        filtered = [
            m for m in all_messages 
            if m['recipient'].lower() == recipient_lower or m['recipient'].lower() == 'all'
        ]
        
        # Filter by since_id if provided
        if since_id:
            found_index = -1
            for i, m in enumerate(filtered):
                if m['message_id'] == since_id:
                    found_index = i
                    break
            if found_index != -1:
                return filtered[found_index + 1:]
                
        return filtered

    def clear_old_messages(self, days: int = 7):
        """Clean up old messages (not implemented for now)"""
        pass

if __name__ == "__main__":
    # Simple test
    manager = MessagingManager(".")
    msg_id = manager.send_message("AgentA", "AgentB", "Hello from A!")
    print(f"Sent message: {msg_id}")
    
    msgs = manager.get_messages("AgentB")
    print(f"Messages for AgentB: {msgs}")
