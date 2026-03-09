# Project: basefunctions

## Description
Die Lib ist eine Sammlung von unterschiedlichen Funktionalitäten für unterschiedliche Bereiche der python Programmierung. Hier sind sämtliche Basisdienste vorhanden, die wir aktuell gebraucht haben, besonders der EventBus Mechanismus ist hier hervorzuheben, ein multithreaded Event Deploy Mechanismus mit hoher Performance.

## Core Value
Sammlung von unterschiedlichen Basisfunktionen für meine python Implementierungen

## Requirements

### Must Have
- ✓ update_packages schützt editable installs (pip install -e .) vor Überschreiben — Phase 01-01

### Should Have
- ✓ Ausführliche User-Dokumentation für das runtime Subpackage — Phase 01-02
- ✓ Vollständige System-Dokumentation für basefunctions.runtime (interne Architektur) — Phase 01-03

### Nice to Have
- [To be defined during planning]

## Constraints
- Standalone-Script `bin/update_packages.py` darf keine basefunctions-Abhängigkeit haben (self-contained)

## Key Decisions

| Decision | Rationale | Phase |
|----------|-----------|-------|
| Editable install detection via `venv_path.parents` statt CWD | CWD ist fragil — Venv-Path ist kanonisch | 01-01 |
| `_find_development_path()` als Standard für Dev-Dir-Erkennung | Bereits in runtime_functions.py etabliert | 01-01 |
| Complete rewrite von runtime.md statt Patch | Signatures waren falsch, Algorithmen fehlten — Patch hätte Lücken gelassen | 01-02 |
| python_doc_agent für System-Doku-Erstellung | Spezialisierter Agent mit vollständigem Source-Kontext, folgt system_documentation.md Template | 01-03 |

## Success Criteria
- Sammlung von unterschiedlichen Basisfunktionen für meine python Implementierungen is achieved
- update_packages überschreibt keine editable installs ✓ (Phase 01-01)

## Specialized Flows

See: .paul/SPECIAL-FLOWS.md

Quick Reference:
- /python:python_code_skill → Python-Implementierungen

---
*Created: 2026-03-03 | Last updated: 2026-03-09 after Phase 01-03*
