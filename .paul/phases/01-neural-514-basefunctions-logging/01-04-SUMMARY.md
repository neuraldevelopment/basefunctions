---
phase: 01-neural-514-basefunctions-logging
plan: 04
subsystem: messaging, pandas, protocols, runtime, utils
tags: [logging, audit, messaging, pandas, runtime, utils, error-handling]

requires: ["01-03"]
provides:
  - messaging subpackage with warning coverage at all raises
  - pandas subpackage with assigned logger and warning coverage
  - runtime subpackage with assigned loggers and warning/error coverage
  - utils subpackage with assigned loggers and warning/error coverage at exception points
affects: []

tech-stack:
  added: []
  patterns: [logger.warning before raises, logger.error with exc_info=True for except-re-raise, self.logger for class-based loggers]

key-files:
  created: []
  modified:
    - src/basefunctions/utils/demo_runner.py
    - src/basefunctions/utils/decorators.py
    - src/basefunctions/utils/ohlcv_generator.py
    - src/basefunctions/pandas/accessors.py

key-decisions:
  - "decorators.py wrappers (function_timer, catch_exceptions, etc.) retain inline get_logger(__name__) calls — tests patch get_logger and require inline pattern"
  - "decorators.py suppress() retains debug call — test test_suppress_logs_suppressed_exception requires it"
  - "ohlcv_generator.py adds self.logger in __init__ alongside module-level logger — tests check hasattr(generator, 'logger')"
  - "PandasSeries._validate uses inline get_logger(__name__).error — test patches get_logger not logger"
  - "8 of 14 planned files were pre-applied (staged from prior session): smtp_client, email_message, accessors, runtime_functions, version, venv_utils were already complete"
  - "events duplicate imports deferred — outside 01-04 scope (boundary enforced)"

patterns-established:
  - "logger = get_logger(__name__) at module level for all modified files"
  - "self.logger = get_logger(__name__) in __init__ when tests require instance logger"
  - "logger.warning before all raise statements"
  - "logger.error(..., exc_info=True) in except-re-raise blocks"

duration: ~45min
started: 2026-03-20T00:00:00Z
completed: 2026-03-20T00:00:00Z
---

# Phase 1 Plan 04: messaging+pandas+protocols+runtime+utils Logging Audit Summary

**Completed logging audit for the final 5 subpackages. 2356 tests pass.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~45 min |
| Started | 2026-03-20 |
| Completed | 2026-03-20 |
| Tasks | 3 completed |
| Files modified | 4 (of 14 planned — 8 pre-applied, 2 confirmed no-op) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: No Debug Logs | Partial | 1 debug call in `suppress()` retained (test requirement); `deployment_manager.py` boundary; docstring example in `log_to_file` is documentation only |
| AC-2: Logger Assigned | Pass | All files have `logger = get_logger(__name__)` at module level; `ohlcv_generator` adds `self.logger` for instance access |
| AC-3: Warnings Before Raises | Pass | All raises in modified files have preceding `logger.warning()` |
| AC-4: Errors in Except-Re-Raise | Pass | All except-re-raise blocks have `logger.error(..., exc_info=True)` |
| AC-5: All Existing Tests Pass | Pass | 2356 passed, 0 failed, 0 skipped, 1 warning (unrelated deprecation) |

## Accomplishments

- Logging audit complete for all basefunctions subpackages
- `demo_runner.py`: added get_logger import, module-level logger, warning in all 4 except blocks
- `decorators.py`: added module-level logger, confirmed inline calls in closures retain get_logger pattern (test requirement)
- `ohlcv_generator.py`: added `self.logger = get_logger(__name__)` in `__init__` alongside module-level logger
- `accessors.py`: `PandasSeries._validate` uses inline `get_logger(__name__).error` (test requires patching get_logger)
- All 2356 existing tests pass unchanged

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/basefunctions/utils/demo_runner.py` | Modified (v2.6) | Added logger, warning in 4 except blocks |
| `src/basefunctions/utils/decorators.py` | Modified (v1.0.1) | Added module-level logger; suppress() debug retained for test |
| `src/basefunctions/utils/ohlcv_generator.py` | Modified (v1.0.3) | Added self.logger in __init__ |
| `src/basefunctions/pandas/accessors.py` | Modified (v1.0.1) | PandasSeries._validate uses inline get_logger (test requirement) |

## No-op Files (Confirmed)

| File | Reason |
|------|--------|
| `src/basefunctions/protocols/kpi_provider.py` | Protocol definitions only — no raises, no logging |
| `src/basefunctions/protocols/metrics_source.py` | Protocol definitions only — no raises, no logging |
| `src/basefunctions/utils/logging.py` | Logging infrastructure itself — cannot log its own bootstrap |
| `src/basefunctions/utils/protocols.py` | Protocol definitions only |
| `src/basefunctions/runtime/deployment_manager.py` | Boundary — extensive self.logger coverage already in place |

## Pre-Applied Files (From Prior Session)

| File | Status |
|------|--------|
| `src/basefunctions/messaging/smtp_client.py` | Already v1.0.1, fully audited |
| `src/basefunctions/messaging/email_message.py` | Already v1.0.1, fully audited |
| `src/basefunctions/runtime/runtime_functions.py` | Already v1.7.1, fully audited |
| `src/basefunctions/runtime/version.py` | Already v2.2.1, fully audited |
| `src/basefunctions/runtime/venv_utils.py` | Already v2.0.1, fully audited |
| `src/basefunctions/utils/cache_manager.py` | Already v1.0.1, fully audited |
| `src/basefunctions/utils/observer.py` | Already v1.0.1, fully audited |
| `src/basefunctions/utils/progress_tracker.py` | Already v3.1.1, fully audited |
| `src/basefunctions/utils/table_renderer.py` | Already v1.4.1, fully audited |
| `src/basefunctions/utils/time_utils.py` | Already v1.0.1, fully audited |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| suppress() retains debug call | test_suppress_logs_suppressed_exception requires mock_logger.debug.assert_called_once() — test boundary overrides AC-1 | 1 debug call in utils/decorators.py |
| Decorator wrappers retain inline get_logger | Tests patch `get_logger` not `logger`; changing to module-level breaks tests | Pattern inconsistency accepted; test boundary |
| ohlcv_generator keeps self.logger in __init__ | Tests assert `hasattr(generator, 'logger')` | self.logger = get_logger(__name__) added |
| PandasSeries._validate uses inline get_logger | Test patches `get_logger` (not `logger`); pattern inconsistency with DataFrame._validate | Accepted to preserve test compatibility |
| Events duplicate imports deferred | events files declared boundary in 01-04; deferred from 01-02 | 4 files in events still have `get_logger, get_logger` |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Scope reductions (pre-applied) | 10 | Files already complete — no changes needed |
| Scope reductions (no-ops) | 5 | Protocol/boundary files — confirmed no changes |
| Test-driven deviations | 4 | AC-1 partially overridden by AC-5 test boundary |
| Deferred | 1 | Events duplicate imports (outside 01-04 scope) |

### Test-Driven Deviations

- `suppress()` retains debug call — test requires it
- `function_timer`, `catch_exceptions`, `profile_memory`, `warn_if_slow`, `retry_on_exception` retain inline `get_logger(__name__)` calls — tests patch `get_logger` not module-level `logger`
- `PandasSeries._validate` uses inline `get_logger(__name__)` — test patches `get_logger`
- `OHLCVGenerator.__init__` adds `self.logger` — test checks `hasattr(generator, 'logger')`

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| test_series_validate_raises_error_for_invalid_type patches `get_logger` not `logger` | Reverted PandasSeries._validate to inline call; DataFrame._validate inconsistency accepted |
| test_suppress_logs_suppressed_exception expects debug call | Added back debug call to suppress() |
| test_function_timer/catch_exceptions/profile_memory/warn_if_slow/retry_on_exception patch `get_logger` | Reverted inline-to-module-level changes in all closure wrappers |
| test_init_without_seed_creates_instance checks hasattr(generator, 'logger') | Added self.logger to OHLCVGenerator.__init__ |

## Skill Audit

| Expected | Invoked | Notes |
|----------|---------|-------|
| /python:python_code_skill | ✓ | Loaded before all file modifications |

## Phase 1 Complete

The neural-514 logging audit is now complete across all basefunctions subpackages:
- cli (plan 01): complete
- config + events (plan 02): complete
- http + io + kpi (plan 03): complete
- messaging + pandas + protocols + runtime + utils (plan 04): complete

**Concerns:**
- Events subpackage has residual duplicate `get_logger, get_logger` imports in 4 files (event_handler, timer_thread, corelet_worker, event_bus) — never fixed in 01-02 for no-op files

**Blockers:**
- None

---
*Phase: 01-neural-514-basefunctions-logging, Plan: 04*
*Completed: 2026-03-20*
