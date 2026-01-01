import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.tools import FunctionTool
from sprint_tools import update_sprint_task_status, worker_tools

async def main():
    print("Initializing...")
    session_service = InMemorySessionService()
    
    # Test 1: Can we create an agent with the tool?
    try:
        tools = [FunctionTool(update_sprint_task_status)]
        agent = LlmAgent(name="TestAgent", instruction="Test", model="gemini-1.5-pro-preview-0409", tools=tools)
        print("Agent created.")
    except Exception as e:
        print(f"Agent creation failed: {e}")
        return

    # Test 2: Can we run the tool?
    # We won't actually call the LLM to avoid cost/time, just check if Runner init works.
    try:
        await session_service.create_session("App", "User", "Session1")
        runner = Runner(app_name="App", agent=agent, session_service=session_service)
        print("Runner created.")
    except Exception as e:
        print(f"Runner creation failed: {e}")

    # Test 3: Can we call the async function directly?
    try:
        res = await update_sprint_task_status("doesntexist", "[x]")
        print(f"Direct call result: {res}")
    except Exception as e:
        print(f"Direct call failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
