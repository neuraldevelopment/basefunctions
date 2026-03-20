---
phase: 01-neural-514-basefunctions-logging
plan: 02
subsystem: config, events
tags: [logging, audit, config, events, error-handling]

requires: []
provides:
  - config subpackage with zero debug/critical logs and warning coverage at raises
  - events subpackage with zero debug logs and full error/warning coverage at exception points
affects: [03-neural-514-basefunctions-logging-http-io-kpi, 04-neural-514-basefunctions-logging-messaging-pandas-protocols-runtime-utils]

tech-stack:
  added: []
  patterns: [logger.warning before ValueError raises, logger.error with exc_info=True for unrecoverable failures]

key-files:
  created: []
  modified:
    - src/basefunctions/config/config_handler.py
    - src/basefunctions/config/secret_handler.py
    - src/basefunctions/events/event_bus.py
    - src/basefunctions/events/corelet_worker.py
    - src/basefunctions/events/event.py
    - src/basefunctions/events/event_factory.py
    - src/basefunctions/events/ticked_rate_limiter.py

key-decisions:
  - "4 of 11 planned files had no changes needed (event_context, event_exceptions, event_handler, timer_thread)"
  - "timer_thread.py critical() calls kept - multi-thread corruption is a genuine system-threatening condition"
  - "config_handler.py critical→error: config file operation failures are recoverable, not system-threatening"

patterns-established:
  - "logger.warning before raise ValueError (validation failures)"
  - "logger.error(..., exc_info=True) in except blocks that swallow or re-raise exceptions"
  - "logger.critical() only for true system-integrity failures (e.g., multi-thread corruption)"

duration: ~30min
started: 2026-03-19T00:00:00Z
completed: 2026-03-19T00:00:00Z
---

# Phase 1 Plan 02: config+events Logging Audit Summary

**Removed all debug logs, demoted inappropriate critical calls, and added error/warning coverage across 7 config+events files; 360 tests pass.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~30 min |
| Started | 2026-03-19 |
| Completed | 2026-03-19 |
| Tasks | 2 completed |
| Files modified | 7 (of 11 planned) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: No Debug Logs Remain | Pass | `grep -rn "logger.debug\|_logger.debug" src/basefunctions/config/ src/basefunctions/events/` → 0 results |
| AC-2: No Misused Critical Logs | Pass | config: 0 critical calls remain; events: timer_thread critical() kept (multi-thread corruption) |
| AC-3: Exceptions Logged at Correct Severity | Pass | All uncovered except blocks now have error/warning before fallback or re-raise |
| AC-4: Validation Failures Logged | Pass | logger.warning before all ValueError raises in config_handler, event.py, event_factory, ticked_rate_limiter |
| AC-5: Existing Tests Pass | Pass | 360 passed, 0 failed, 0 skipped, 0 warnings |

## Accomplishments

- Zero `logger.debug()` / `_logger.debug()` calls remain in config and events subpackages
- 2x `logger.critical()` in config_handler.py demoted to `logger.error()` (config failures are recoverable)
- 13 `logger.warning()` / `logger.error()` calls added at exception and validation failure points
- All 360 existing tests pass unchanged — no behavior changes introduced

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/basefunctions/config/config_handler.py` | Modified (v3.3) | critical→error (2x), warning before raises (3x), duplicate import removed |
| `src/basefunctions/config/secret_handler.py` | Modified (v1.1) | Duplicate import removed |
| `src/basefunctions/events/event_bus.py` | Modified (v1.2.2) | Removed 2 debug calls |
| `src/basefunctions/events/corelet_worker.py` | Modified (v1.2) | Removed 7 debug calls (including inner signal_handler and finally block) |
| `src/basefunctions/events/event.py` | Modified (v1.3) | Warning before 2 raises, warning for uncovered except block |
| `src/basefunctions/events/event_factory.py` | Modified (v2.1) | Warning before 5 raises, error before RuntimeError re-raise |
| `src/basefunctions/events/ticked_rate_limiter.py` | Modified (v1.0.3) | Warning before 5 raises |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| timer_thread.py critical() kept | Multi-thread corruption (PyThreadState_SetAsyncExc affecting >1 thread) is a genuine system-integrity failure — comment confirms "should never happen" | Consistent with log level guide: critical=system cannot continue |
| config_handler.py critical→error | Config file operation failures are recoverable (caller can retry or use defaults) | Aligns with log level guide: error=unrecoverable within operation, but application continues |
| 4 files not modified (event_context, event_exceptions, event_handler, timer_thread) | event_context/exceptions: no exception handlers or raises; event_handler: already fully covered; timer_thread: critical() is intentional | Scope reduced from 11 to 7 files; criteria still fully met |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Scope reductions | 4 | No-op files excluded; criteria met |
| Auto-fixed | 0 | — |
| Deferred | 0 | — |

**Total impact:** Minor scope reduction — 4 files had no logging issues; zero regressions.

### Scope Reductions

- `event_context.py`: No exception handlers, no raises, no debug calls — no changes needed
- `event_exceptions.py`: Exception class definitions only — no changes needed
- `event_handler.py`: Already fully covered (warning/error at all exception points)
- `timer_thread.py`: critical() calls are intentional (kept per plan boundaries)

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| corelet_worker.py finally block became empty after removing debug call | Added `pass` to maintain valid syntax |

## Skill Audit

| Expected | Invoked | Notes |
|----------|---------|-------|
| /python:python_code_skill | ✓ | Loaded before all file modifications |

## Next Phase Readiness

**Ready:**
- Logging pattern fully established across cli, config, events: logger.error for unrecoverable, logger.warning before raises
- Plans 03 and 04 can follow the same pattern with high confidence

**Concerns:**
- None

**Blockers:**
- None

---
*Phase: 01-neural-514-basefunctions-logging, Plan: 02*
*Completed: 2026-03-19*
