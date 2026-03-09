# Context: Phase 01-01 — update_packages Editable Install Fix

**Created:** 2026-03-09
**Source:** /paul:discuss session

## Goals

1. `update_packages` schließt Packages aus, deren Venv innerhalb eines Development-Directories liegt — unabhängig vom CWD
2. Erkennungsmethode basiert auf dem runtime-Standard: `_find_development_path(pkg_name)` → Venv-Path prüfen
3. Fix gilt für beide Modi: `update_single_venv()` und `update_all_deployments()`

## Problem

In `update_single_venv()` (Zeilen 705–719) wird der "current package" via CWD erkannt:
```python
cwd = Path.cwd()
if dev_path_resolved in cwd.parents:  # ← CWD-abhängig, fragil
    current_package = pkg_name
```

Ist der User in einem anderen Verzeichnis, aber hat das basefunctions-Dev-Venv aktiv → `current_package = None` → basefunctions landet in `to_check` → editable install wird überschrieben.

## Korrekte Erkennung (Standard)

Prüfe ob die zu aktualisierende **Venv-Path** innerhalb eines Development-Directories liegt:
```python
dev_paths = _find_development_path(pkg_name)
for dev_path in dev_paths:
    if Path(dev_path).resolve() in venv_path.parents:
        # Diese Venv ist die Dev-Venv für pkg_name → ausschließen
```

`_find_development_path()` ist bereits im Script vorhanden (standalone-Implementierung).

## Approach

- Minimaler Fix, nur die Erkennungslogik ändern
- `update_single_venv()`: venv_path statt cwd vergleichen
- `update_all_deployments()`: gleiche Prüfung pro Deployment-Venv
- TDD: erst failing tests, dann fix
- Kein Refactoring darüber hinaus

## Open Questions

Keine.
