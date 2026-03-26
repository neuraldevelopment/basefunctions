---
phase: 02-neural-533-basefunctions-register_package_defaults-requires-only
plan: 01
subsystem: config
tags: [config, api, breaking-change, tdd, monkeypatch]

requires: []
provides:
  - register_package_defaults accepts only package_name — path resolved internally
  - Callers in basefunctions and backtesterfunctions simplified
  - pytest 9.0+ monkeypatch object-form pattern established
affects: [backtesterfunctions, any package calling register_package_defaults]

tech-stack:
  added: []
  patterns:
    - monkeypatch.setattr(module_object, "ATTR", value) — object form required for pytest 9+

key-files:
  modified:
    - src/basefunctions/config/config_handler.py
    - src/basefunctions/__init__.py
    - tests/config/test_config_handler.py
    - tests/runtime/test_runtime_functions.py
    - /Users/neutro2/Code/neuraldev/backtesterfunctions/src/backtesterfunctions/__init__.py

key-decisions:
  - "get_runtime_config_path called inside register_package_defaults — path resolution is context-independent"
  - "monkeypatch string-form fails in pytest 9.0+ for submodule paths — use object form"

patterns-established:
  - "monkeypatch.setattr(_rf_module, 'ATTR', value) — object-form avoids pytest 9 resolution bug"

duration: ~30min
started: 2026-03-26T00:00:00Z
completed: 2026-03-26T00:30:00Z
---

# Phase 2 Plan 01: register_package_defaults API simplification Summary

**`register_package_defaults` simplified to single argument — path resolved internally via `get_runtime_config_path`.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~30 min |
| Started | 2026-03-26 |
| Completed | 2026-03-26 |
| Tasks | 3 completed |
| Files modified | 5 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: New API — single argument | Pass | `register_package_defaults(package_name)` — no second arg |
| AC-2: Behavior preserved — config loaded | Pass | `get_runtime_config_path` called internally, config merged immediately |
| AC-3: Behavior preserved — missing file silent | Pass | No exception when path doesn't exist |
| AC-4: All callers updated | Pass | basefunctions + backtesterfunctions simplified |
| AC-5: All tests pass | Pass | 2355 passed, 0 failed, 0 errors |

## Accomplishments

- `config_handler.py` signature simplified: `register_package_defaults(self, package_name: str) -> None`
- Added `from basefunctions.runtime.runtime_functions import get_runtime_config_path` import to `config_handler.py`
- Both callers simplified: `ConfigHandler().register_package_defaults("basefunctions")`
- All 3 existing register_package_defaults tests updated with `patch("basefunctions.config.config_handler.get_runtime_config_path", ...)`

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/basefunctions/config/config_handler.py` | Modified (v3.6) | Remove config_path param, call get_runtime_config_path internally |
| `src/basefunctions/__init__.py` | Modified | Simplified caller — single arg |
| `tests/config/test_config_handler.py` | Modified | Updated 3 tests to mock get_runtime_config_path, single-arg calls |
| `tests/runtime/test_runtime_functions.py` | Modified | Fixed pre-existing monkeypatch failures (see Deviations) |
| `backtesterfunctions/src/backtesterfunctions/__init__.py` | Modified | Simplified caller + removed unused get_runtime_config_path import |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Import `get_runtime_config_path` at module level in config_handler.py | Allows monkeypatch in tests; no cyclic import risk | Clean testability |
| Keep `get_runtime_config_path` in basefunctions.__all__ | It is a public API used by other packages | No API surface reduction |
| Remove `get_runtime_config_path` import from backtesterfunctions | No longer needed after simplification | Clean imports |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Essential — 34 tests previously failing |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** One out-of-scope fix, essential for clean test suite.

### Auto-fixed Issues

**1. Runtime test monkeypatch failures (pytest 9.0 incompatibility)**
- **Found during:** Task 2 verification
- **Issue:** `monkeypatch.setattr("basefunctions.runtime.runtime_functions.BOOTSTRAP_CONFIG_PATH", ...)` string form fails in pytest 9.0 — resolve algorithm cannot find `runtime_functions` as attribute after already resolving the module
- **Fix:** Added `import basefunctions.runtime.runtime_functions as _rf_module` to test file; replaced all 9 string-form monkeypatch calls with object form: `monkeypatch.setattr(_rf_module, "ATTR", value)`
- **Files:** `tests/runtime/test_runtime_functions.py`
- **Verification:** 38/38 runtime tests pass

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| backtesterfunctions tests fail — deployed basefunctions has old API | Expected — user must run `ppip install basefunctions` to update deployed version |

## Next Phase Readiness

**Ready:**
- Phase 2 complete — cycle-07 can be closed
- All packages using register_package_defaults simplified
- Pattern documented for any future packages

**Concerns:**
- backtesterfunctions tests need `ppip install basefunctions` before they pass against the new API

**Blockers:**
- None

---
*Phase: 02-neural-533-basefunctions-register_package_defaults-requires-only, Plan: 01*
*Completed: 2026-03-26*
