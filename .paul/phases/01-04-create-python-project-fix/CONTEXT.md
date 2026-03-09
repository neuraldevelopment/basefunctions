# Context: Phase 01-04 — create-python-project-fix

**Created:** 2026-03-09
**Source:** /paul:discuss session

## Goals

1. `pip install -e .` muss nach `create_python_project` zuverlässig im neuen `.venv` installiert sein — Fehler darf nicht verschluckt werden
2. Dev/test-Extra-Installation (`.[dev,test]`) als separater Schritt — Fehler toleriert (geloggt), aber kein Abbruch des Primärziels

## Problem

In `bin/create_python_project.py`, Methode `_setup_virtual_environment` (Zeilen 550–553):

```python
except basefunctions.VenvUtilsError as e:
    self.logger.critical(f"Virtual environment setup failed: {e}")
except Exception as e:
    self.logger.critical(f"Virtual environment setup failed: {e}")
```

Kein `raise` nach `logger.critical()` — Exceptions werden geschluckt. `subprocess.run(..., check=True)` wirft bei pip-Fehler `subprocess.CalledProcessError` → als `Exception` gefangen → geloggt → Funktion returned normal → Caller bekommt keinen Fehler. Der User sieht "package created successfully", aber `pip install -e .` wurde nie erfolgreich ausgeführt.

## Korrekte Lösung

Zwei separate Schritte in `_setup_virtual_environment`:

1. **Editable install** (`pip install -e .`) — mandatory, Exception propagiert nach außen
2. **Dev extras** (`pip install -e ".[dev,test]"`) — optional, Fehler wird geloggt, aber kein raise

## Approach

- Minimaler Fix: nur `_setup_virtual_environment` umstrukturieren
- Editable install und dev-extras trennen
- Editable install: Exception MUSS re-raised werden (fail hard)
- Dev extras: Exception wird geloggt, nicht re-raised
- TDD: erst failing tests, dann fix
- Kein Refactoring darüber hinaus

## Open Questions

Keine.
