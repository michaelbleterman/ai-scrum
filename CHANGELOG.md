# Changelog

## [Unreleased] - Framework Fixes

### Added
- **Safety Limits**: Added `max_turns` (default 20) to QA, Demo, and Retro phases in `parallel_sprint_runner.py` to prevent infinite loops.
- **Sprint Status Sync**: The runner now automatically updates the `SPRINT_XXX.md` header status (Planning -> In Progress -> QA -> Review) at each phase transition.
- **Strict Definition of Done (DoD)**: Updated Backend and Frontend agent prompts to explicitly forbid marking tasks as complete if they contain `TODO`s or are unverified.
- **Defect Reporting**: Updated QA Agent prompt to enforce `DEFECT:` prefix for reported issues, ensuring they are correctly assigned for the next loop.

### Changed
- **Backup Logic**: Disabled automatic `.backup` file creation in `sprint_tools.py` to reduce workspace clutter.
- **Demo Interaction**: `run_demo_phase` now defaults to non-interactive mode if no valid TTY is detected, preventing background jobs from hanging on `input()`.

### Verification
- Added `tests/test_resume_sprint.py` to verify resume logic and state preservation.
- Validated full lifecycle (Execution -> QA -> Fix -> Retro) via `tests/test_e2e_real.py`.
