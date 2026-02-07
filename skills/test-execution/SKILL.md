---
name: Test Execution
description: Strategies for running tests including inline, pytest, and Playwright
---

# Test Execution Skill

This skill provides test execution strategies for different project types.

## When to Use
- QA verification of completed tasks
- Running unit/integration/e2e tests
- Debugging test failures

## Strategy 1: Inline Test (Script/Library Projects)

Best for simple validation without import complexity.

```python
# Create test in SAME directory as code
write_file("project_tracking/test_inline.py", """
from dummy_math import add  # No import issues - same directory!

result = add(2, 3)
expected = 5

if result == expected:
    print(f"✅ PASS: add(2, 3) = {result}")
    exit(0)
else:
    print(f"❌ FAIL: add(2, 3) = {result}, expected {expected}")
    exit(1)
""")

# Run from correct directory
run_command("cd project_tracking && python test_inline.py")
```

## Strategy 2: Pytest (Standard Projects)

```bash
# Run specific test file
pytest tests/test_feature.py -v

# Run with pattern matching
pytest -k "test_user" -v

# Run with coverage
pytest --cov=src tests/
```

## Strategy 3: Playwright (Web UI Testing)

**CRITICAL**: Always use headless mode for autonomous execution.

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    headless: true,  // MANDATORY - never false
    baseURL: 'http://localhost:5173',
  },
});
```

```bash
# Run tests
npx playwright test

# NEVER use these flags:
# --headed (opens browser)
# --debug (opens inspector)
```

## Circuit Breaker Pattern

**Max 3 retries** for same error:

1. Attempt 1: pytest → ModuleNotFoundError
2. Attempt 2: sys.path fix → ModuleNotFoundError  
3. Attempt 3: importlib → ModuleNotFoundError
4. **STOP** → Switch to inline strategy

## Failure Investigation

When test fails, categorize:

| Category | Action |
|----------|--------|
| Environment Issue | Mark BLOCKED, document |
| Test Code Issue | Fix test, re-run |
| Application Defect | Create DEFECT task |

## Evidence Logging

Always include test output in completion:
```
VERIFIED:
- pytest tests/test_auth.py: 5 passed, 0 failed
- Coverage: 87%
```
