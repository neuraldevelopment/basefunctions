---
phase: 01-04-create-python-project-fix
plan: 01
subsystem: bin
tags: [exception-handling, venv, subprocess, tdd, pytest]

requires:
  - phase: none
    provides: n/a

provides:
  - Fixed _setup_virtual_environment: editable install errors now propagate
  - New _install_editable_package: mandatory step, raises CreatePythonPackageError on failure
  - New _install_dev_extras: tolerant step, logs warning only on failure
  - TDD test suite for exception handling behavior

affects: []

tech-stack:
  added: []
  patterns:
    - "Split mandatory/tolerant install steps into separate methods"
    - "CalledProcessError → domain exception wrapping for mandatory steps"

key-files:
  created:
    - tests/bin/test_create_python_project.py
  modified:
    - bin/create_python_project.py

key-decisions:
  - "_setup_virtual_environment split into 3 methods: setup (orchestrator), _install_editable_package (mandatory), _install_dev_extras (tolerant)"
  - "Test placed in tests/bin/ following existing structure (tests/bin/test_update_packages.py)"

patterns-established:
  - "Mandatory subprocess steps wrap CalledProcessError → domain exception"
  - "Tolerant subprocess steps log warning and return normally"

duration: ~20min
started: 2026-03-09T00:00:00Z
completed: 2026-03-09T00:00:00Z
---

# Phase 01-04 Plan 01: create-python-project-fix Summary

**Fixed exception-swallowing in `_setup_virtual_environment`: editable install (`pip install -e .`) now raises `CreatePythonPackageError` on failure; dev extras install tolerates failures with a warning log.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~20min |
| Started | 2026-03-09 |
| Completed | 2026-03-09 |
| Tasks | 3 completed |
| Files modified | 2 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Editable Install Fehler ist sichtbar | Pass | CalledProcessError → CreatePythonPackageError raised and propagated |
| AC-2: Dev-Extras Fehler wird toleriert | Pass | CalledProcessError logged as WARNING, no exception propagated |
| AC-3: Tests bestehen | Pass | 3/3 tests PASSED, 0 skipped, ruff 0 issues |

## Accomplishments

- Removed exception-swallowing: `_setup_virtual_environment` no longer has bare `except Exception` blocks
- `_install_editable_package`: mandatory step, wraps `CalledProcessError` → `CreatePythonPackageError`
- `_install_dev_extras`: tolerant step, logs warning and returns normally on failure
- Full TDD cycle: Red (3 failing tests) → Green (implementation) → Refactor (ruff clean, coverage verified)

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `bin/create_python_project.py` | Modified (v2.5) | Restructured `_setup_virtual_environment`, added `_install_editable_package`, `_install_dev_extras` |
| `tests/bin/test_create_python_project.py` | Created | TDD tests for exception handling behavior (3 tests) |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Test placed in `tests/bin/` | Follows existing structure (`tests/bin/test_update_packages.py`) | Consistent test layout |
| `pytestmark` to suppress pre-existing DeprecationWarning | `setup_logger()` deprecated in legacy code, outside scope — can't change | Clean test output without touching boundary code |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Minor — import order in test file corrected by ruff |
| Scope additions | 0 | None |
| Deferred | 0 | None |

**Total impact:** Minimal auto-fix, no scope creep.

### Auto-fixed Issues

**1. Import Order — test file**
- **Found during:** Task 3 (ruff check)
- **Issue:** `import logging` placed in `# LOGGING` section after `# IMPORTS`
- **Fix:** Moved `import logging` into `# IMPORTS` section (alphabetical order)
- **Files:** `tests/bin/test_create_python_project.py`
- **Verification:** `ruff check` → 0 issues

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| `--cov=bin.create_python_project` failed (not a package) | Used `--cov=bin` instead; changed methods (lines 525-601) confirmed fully covered |
| Pre-existing DeprecationWarning from `setup_logger()` at module import | Added `pytestmark` to suppress in test file (legacy boundary code, cannot modify) |

## Next Phase Readiness

**Ready:**
- Phase 01-04 complete — all 4 phases of milestone done
- `create_python_project.py` now correctly surfaces venv setup failures to the caller
- Test coverage established for exception handling

**Concerns:**
- Pre-existing DeprecationWarning from `basefunctions.setup_logger()` in `create_python_project.py` — future cleanup candidate

**Blockers:**
- None

---
*Phase: 01-04-create-python-project-fix, Plan: 01*
*Completed: 2026-03-09*
