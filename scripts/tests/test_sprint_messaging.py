import pytest
import os
import shutil
import json
from pathlib import Path
from scripts.sprint_messaging import MessagingManager, Message

@pytest.fixture
def temp_project_root(tmp_path):
    root = tmp_path / "test_project"
    root.mkdir()
    return str(root)

def test_message_creation():
    msg = Message(sender="AgentA", recipient="AgentB", content="Hello", message_type="info")
    assert msg.sender == "AgentA"
    assert msg.recipient == "AgentB"
    assert msg.content == "Hello"
    assert msg.message_type == "info"
    assert msg.timestamp != ""
    assert msg.message_id.startswith("msg_")

def test_send_receive_message(temp_project_root):
    manager = MessagingManager(temp_project_root)
    
    # Send message
    msg_id = manager.send_message("AgentA", "AgentB", "Hello AgentB", "request")
    assert msg_id.startswith("msg_")
    
    # Receive message for AgentB
    messages = manager.get_messages("AgentB")
    assert len(messages) == 1
    assert messages[0]['content'] == "Hello AgentB"
    assert messages[0]['sender'] == "AgentA"
    
    # Receive message for AgentA (should be empty)
    messages_a = manager.get_messages("AgentA")
    assert len(messages_a) == 0

def test_broadcast_message(temp_project_root):
    manager = MessagingManager(temp_project_root)
    
    manager.send_message("Orchestrator", "all", "Sprint Started")
    
    # Both agents should see it
    msgs_a = manager.get_messages("AgentA")
    msgs_b = manager.get_messages("AgentB")
    
    assert len(msgs_a) == 1
    assert len(msgs_b) == 1
    assert msgs_a[0]['content'] == "Sprint Started"
    assert msgs_b[0]['content'] == "Sprint Started"

def test_since_id_filtering(temp_project_root):
    manager = MessagingManager(temp_project_root)
    
    id1 = manager.send_message("A", "B", "Msg 1")
    id2 = manager.send_message("A", "B", "Msg 2")
    id3 = manager.send_message("A", "B", "Msg 3")
    
    # Get all
    all_msgs = manager.get_messages("B")
    assert len(all_msgs) == 3
    
    # Get since id1
    since_id1 = manager.get_messages("B", since_id=id1)
    assert len(since_id1) == 2
    assert since_id1[0]['message_id'] == id2
    assert since_id1[1]['message_id'] == id3
    
    # Get since id2
    since_id2 = manager.get_messages("B", since_id=id2)
    assert len(since_id2) == 1
    assert since_id2[0]['message_id'] == id3
    
    # Get since id3
    since_id3 = manager.get_messages("B", since_id=id3)
    assert len(since_id3) == 0

def test_concurrent_write_safety(temp_project_root):
    # This is a basic test for the implementation, actual concurrency testing is hard in unit tests
    # but we can verify the file is correctly updated and read.
    manager = MessagingManager(temp_project_root)
    
    for i in range(10):
        manager.send_message("AgentA", "AgentB", f"Message {i}")
        
    messages = manager.get_messages("AgentB")
    assert len(messages) == 10
    for i in range(10):
        assert messages[i]['content'] == f"Message {i}"
