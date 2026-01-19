
import os
import sys
import shutil
import tempfile
import logging
import contextvars
from pathlib import Path

# Add scripts dir to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

from sprint_messaging import MessagingManager
from sprint_tools import list_dir, current_messaging_context

def test_message_injection():
    print("--- Starting Message Injection Test ---")
    
    # 1. Setup Request/Temp Environment
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"[Setup] Created temp dir: {temp_dir}")
        
        # Initialize Messaging Manager
        manager = MessagingManager(temp_dir)
        recipient_role = "Worker"
        
        # 2. Set Context (simulating the Worker running)
        print(f"[Setup] Setting active context for role: @{recipient_role}")
        token = current_messaging_context.set({
            "manager": manager,
            "role": recipient_role,
            "seen_ids": set()
        })
        
        try:
            # 3. Simulate "Agent B" sending a message to "Agent A" (Worker)
            sender = "Orchestrator"
            content = "STOP! Priority change."
            print(f"[Action] @{sender} sending message to @{recipient_role}: '{content}'")
            mid = manager.send_message(sender, recipient_role, content)
            print(f"[Debug] Sent message ID: {mid}")
            
            # Verify persistence
            all_raw = manager._read_messages()
            print(f"[Debug] Raw messages in file: {all_raw}")
            
            check_msgs = manager.get_messages(recipient_role)
            print(f"[Debug] Check messages for {recipient_role}: {check_msgs}")
            
            # 4. Agent A (Worker) calls a tool
            print("[Action] @Worker calling tool 'list_dir'...")
            # We assume list_dir is decorated with @log_tool_usage which has our logic
            # We pass the temp_dir so it actually lists something valid and doesn't error out
            result = list_dir(temp_dir)
            
            print("\n--- Tool Output ---")
            print(result)
            print("-------------------\n")
            
            # 5. Verify Injection
            if "=== 🔔 NEW MESSAGES RECEIVED ===" in str(result) and content in str(result):
                print("✅ TEST PASSED: Message was successfully injected into tool output.")
            else:
                print("❌ TEST FAILED: Message NOT found in tool output.")
                sys.exit(1)
                
            # 6. Verify subsequent calls don't show it again (deduplication)
            print("\n[Action] Calling tool again (should be clean)...")
            result_2 = list_dir(temp_dir)
            if "=== 🔔 NEW MESSAGES RECEIVED ===" in str(result_2):
                print("❌ TEST FAILED: Message was re-injected (deduplication failed).")
                print(result_2)
                sys.exit(1)
            else:
                print("✅ TEST PASSED: Message was correctly deduplicated.")

        finally:
            current_messaging_context.reset(token)

if __name__ == "__main__":
    # Configure logging to show info so we see the tool logs too
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    test_message_injection()
