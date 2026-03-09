# Summary: Phase 01-01 — update_packages Editable Install Fix

**Completed:** 2026-03-09
**Plan:** 01-01-PLAN.md

## What Was Built

Bugfix in `bin/update_packages.py`: Die fehlerhafte CWD-basierte Erkennung von "eigenem Package" wurde durch eine zuverlässige venv-path-basierte Erkennung ersetzt.

### Neue Funktion: `_is_editable_in_venv(pkg_name, venv_path)`

Prüft ob ein Package als editable install in einem Venv vorliegt, indem überprüft wird ob `venv_path.resolve()` innerhalb des Development-Directories des Packages liegt (via `_find_development_path()`).

### Fix `update_single_venv()`

Vorher (buggy): CWD gegen dev-paths geprüft → fragil wenn User in anderem Verzeichnis
Nachher: `editable_packages` set via `_is_editable_in_venv()` → venv-path-basiert, CWD-unabhängig

### Fix `update_all_deployments()`

`to_check` filter ergänzt um `not _is_editable_in_venv(pkg, venv_path)` als defensive Prüfung.

## Files Modified

- `bin/update_packages.py` — v2.1 (Fix + neue Hilfsfunktion)
- `tests/bin/test_update_packages.py` — v1.1.0 (4 neue Tests)

## Test Results

15/15 Tests grün, zero skipped, zero warnings. Ruff: no issues.

**Neue Tests:**
- `test_update_single_venv_excludes_dev_package_when_cwd_is_different_directory` (AC-1)
- `test_update_single_venv_updates_other_packages_when_dev_package_excluded` (AC-3)
- `test_is_editable_in_venv_returns_true_when_venv_inside_dev_dir` (AC-5)
- `test_is_editable_in_venv_returns_false_when_venv_outside_dev_dir` (AC-5)

## Decisions Made

- CWD-basierter Block (Zeilen 687-694) wurde entfernt — durch `editable_packages`-Logik implizit abgedeckt
- Standard: `find_development_path()` als zuverlässige Erkennungsgrundlage

## Quality Score: 9.5/10.0
