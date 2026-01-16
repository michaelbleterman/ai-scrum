# Demo Walkthrough

**Disclaimer:** This walkthrough is based on the mock components (`dummy_api.py` and `dummy_ui.txt`) created during a previous sprint. The full application is currently not runnable, as noted in the `QA_REPORT.md`. This demo shows the intended functionality of the mock services.

## 1. Backend API

The backend is a simple Python script that provides a status endpoint.

**To run the API:**
```bash
python project_tracking/dummy_api.py
```

**Expected Output:**
```
OK
```
This indicates that the backend service is running and responsive.

## 2. Frontend UI

The frontend is a simple text file that indicates the UI has loaded.

**To view the UI:**
```bash
cat project_tracking/dummy_ui.txt
```

**Expected Output:**
```
UI Loaded
```
This confirms that the frontend component has been successfully loaded.

## Summary

This demo shows that the basic components of the application have been mocked up and are ready for further development. The next step is to replace these mock components with a full-fledged FastAPI backend and a React frontend.
