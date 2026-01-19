# Test Strategy for Sprint Framework

This document outlines the testing strategy for the autonomous sprint framework, organized into three tiers for optimal CI/CD integration.

## Test Tiers

### Tier 1: Unit Tests (Fast - Every Commit)
**Target**: <5 seconds total  
**Scope**: Individual component validation with mocked dependencies

- `test_sprint_utils.py` - Task parsing, status updates, file detection
- `test_sprint_memory.py` - Memory bank recall/storage (chromadb)
- `test_sprint_profile.py` - XP tracking, leveling, skill progression
- `test_sprint_guardrails.py` - Input validation, circuit breakers
- `test_sprint_metadata.py` - Turn budget parsing, metadata extraction

**Run Command**: `pytest tests/unit/ -v`

### Tier 2: Smoke Test (Fast - Every Commit)
**Target**: <30 seconds  
**Scope**: Single task execution with all features enabled

- `test_e2e_smoke.py` - Validates core sprint execution
  - Task completion
  - Memory integration
  - Profile tracking
  - Guardrails enforcement
  - Context discovery
  - Turn budget tracking

**Run Command**: `pytest tests/test_e2e_smoke.py -v`

### Tier 3: Integration & E2E Tests (Slow - Nightly/Release)
**Target**: 5-15 minutes  
**Scope**: Full sprint lifecycle and comprehensive validation

- `test_e2e_real.py` - Complete sprint with Dev → QA → Demo → Retro
  - Parallel execution
  - Defect workflow
  - All agent types
  - Complete artifact generation

**Run Command**: `pytest tests/test_e2e_real.py -v`

## CI Configuration

### Pull Request Pipeline
```yaml
# .github/workflows/ci.yml
test-fast:
  runs-on: ubuntu-latest
  steps:
    - name: Run unit tests
      run: pytest tests/unit/ -v
    - name: Run smoke test
      run: pytest tests/test_e2e_smoke.py -v
  # Total time: ~35 seconds
```

### Nightly Pipeline
```yaml
# .github/workflows/nightly.yml
test-comprehensive:
  runs-on: ubuntu-latest
  steps:
    - name: Run all tests
      run: pytest tests/ -v
  # Total time: ~10-20 minutes
```

## Test Fixtures

Located in `tests/fixtures/sprints/`:
- `minimal_sprint.md` - Single task, basic validation
- `defect_workflow_sprint.md` - Intentional bug scenario
- `multi_role_sprint.md` - Parallel execution test
- `blocked_task_sprint.md` - Blocked task handling
- `epic_sprint.md` - Hierarchical task structure

## Running Tests Locally

```bash
# Fast feedback loop (recommended for development)
pytest tests/unit/ tests/test_e2e_smoke.py -v

# Full test suite (before merging)
pytest tests/ -v

# Single test
pytest tests/test_e2e_smoke.py::SmokeTest::test_single_task_execution_with_all_features -v
```

## Success Criteria

### Unit Tests
- All pass in <5 seconds
- No external API calls (mocked)
- 100% code coverage for utilities

### Smoke Test
- Completes in <30 seconds
- Validates all features work together
- Creates real artifacts (not mocked)

### E2E Test
- Full sprint lifecycle completes successfully
- All artifacts generated (QA report, demo, retrospective)
- Defect workflow validated
- No tasks left incomplete

## Debugging Failed Tests

### If smoke test fails:
1. Check `project_tracking/logs/sprint_*.log` for agent execution details
2. Verify `GOOGLE_API_KEY` is set in `.env`
3. Check `profiles.json` and memory files were created

### If E2E test fails:
1. Review individual phase logs (execution, QA, demo, retro)
2. Check sprint file task statuses
3. Validate all expected artifacts were created
4. Look for blocked or failed tasks with `[!]` status

## Future Improvements

- [ ] Add performance benchmarks for agent turn usage
- [ ] Create integration tests for each phase independently
- [ ] Add mutation testing for critical components
- [ ] Implement test coverage reporting in CI
