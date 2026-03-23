# Phase Context: neural-532

**Phase:** 1 — neural-532-basefunctions-deploy-muss-aktuelles-package-als-source
**Created:** 2026-03-23
**Status:** Ready for planning

---

## Problem

`update_packages` (bin/update_packages.py) installiert das aktuelle Package
(das Package, dessen `.venv` aktiv ist) fälschlicherweise als statische Version
aus dem deploy-Verzeichnis (`~/.neuraldevelopment/packages/<pkg>`).

**Beispiel:**
- User arbeitet in `~/Code/neuraldev/backtesterfunctions`, `.venv` aktiv
- `update_packages` läuft: basefunctions wird korrekt von deploy aktualisiert
- backtesterfunctions selbst wird AUCH aus deploy installiert → FALSCH

Das führt dazu, dass Code-Änderungen am aktuellen Package vom eigenen `.venv`
nicht wahrgenommen werden.

---

## Root Cause

`_is_editable_in_venv()` soll das aktuelle Package erkennen und ausschließen.
Die Funktion ruft `_find_development_path(pkg_name)` auf, das nach
`<dev_dir>/<package_name>` sucht (z.B. `~/Code/backtesterfunctions`).

Die tatsächliche Struktur ist `~/Code/neuraldev/backtesterfunctions` —
eine Ebene tiefer. Daher gibt `_find_development_path` eine leere Liste zurück
→ `_is_editable_in_venv` gibt False zurück → Package wird nicht ausgeschlossen.

---

## Goals

1. Das aktuelle Package (dessen `.venv` aktiv ist) darf NIE aus dem
   deploy-Verzeichnis installiert werden
2. Alle anderen Packages (Dependencies) werden weiterhin korrekt aus deploy
   aktualisiert
3. Minimaler, zielgerichteter Fix — kein Overengineering

---

## Approach

**Einfachste Lösung:** In `update_single_venv()` das aktuelle Package direkt
aus dem venv-Pfad ableiten:

```python
current_package_name = venv_path.parent.name  # z.B. "backtesterfunctions"
```

Dieses Package von `to_check` ausschließen — unabhängig von der
`_is_editable_in_venv` Logik.

**Scope:** Nur `bin/update_packages.py` betroffen.
**Tests:** `tests/` — bestehende Teststruktur prüfen/erweitern.

---

## Constraints

- KISSS: Minimaler Fix, keine Abstraktion für Einmallogik
- TDD: Erst failing test, dann Fix
- Keine Änderung an `_is_editable_in_venv` nötig (separate Logik, separates Issue)
