---
name: Defect Handling
description: Test-first bug fixing workflow for DEFECT and BUG tasks
---

# Defect Handling Skill

This skill provides the workflow for fixing bugs using test-driven development.

## When to Use
- Task starts with "DEFECT:" or "BUG:"
- Fixing reported issues from QA

## Workflow

### Step 1: Create Reproduction Test

**CRITICAL**: The test must assert the **CORRECT/EXPECTED** behavior.

```python
# CORRECT - Tests what SHOULD happen
def test_add_returns_correct_sum():
    result = add(2, 3)
    assert result == 5  # Expected behavior

# WRONG - Don't test the buggy value
def test_add_bug():
    result = add(2, 3)
    assert result == -1  # This proves bug exists, not that fix works
```

### Step 2: Run Test → Should FAIL

```bash
pytest tests/test_defect.py -v
# Expected: FAILED (confirms bug exists)
```

### Step 3: Fix the Code

Modify the source to correct the behavior.

### Step 4: Run Test → Should PASS

```bash
pytest tests/test_defect.py -v
# Expected: PASSED (confirms fix works)
```

### Step 5: Log Evidence

Include test output in task completion log:
```
DEFECT FIXED:
- Test: test_add_returns_correct_sum
- Before: FAILED (returned -1)
- After: PASSED (returns 5)
```

## Common Mistakes

❌ **Don't** just verify the bug exists  
❌ **Don't** mark complete without running tests  
❌ **Don't** leave `# TODO: fix later` comments  

✅ **Do** create test with expected behavior  
✅ **Do** show before/after test results  
✅ **Do** run full test suite to check for regressions
