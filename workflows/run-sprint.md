---
description: Trigger the parallel automated sprint execution
---

// turbo-all

This workflow triggers the specialized ADK parallel runner to orchestrate the current sprint tasks.

1. Ensure `GOOGLE_API_KEY` is set in the project `.env` file.
2. Run the following command to start the mission:

```powershell
C:\Users\Michael\.gemini\.agent\scripts\.venv\Scripts\python.exe C:\Users\Michael\.gemini\.agent\scripts\parallel_sprint_runner.py
```
