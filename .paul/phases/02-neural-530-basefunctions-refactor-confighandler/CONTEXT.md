# Phase Context: neural-530-basefunctions-refactor-confighandler

## Goals

- ConfigHandler von "Lib lädt sich selbst" auf "App kontrolliert Loading" umstellen
- 4 deprecated Methoden entfernen, die Deployment-Pfad kennen und Struktur anlegen
- Neues Self-Registration Pattern: Packages registrieren ihre Defaults beim Import
- deep-merge statt shallow-update in load_config_file → App-Werte gewinnen, Defaults bleiben erhalten

## Scope: basefunctions ONLY

Alle anderen Packages (tickerhub, signalengine, etc.) sind TABU in dieser Phase.

## Approved Approach

**Config-Priorität (niedrig → hoch):**
1. Package-Defaults (geladen via register_package_defaults beim Import)
2. App-Config (geladen via load_config_file explizit von der App)

**Self-Registration Flow:**
```
import tickerhub
  → tickerhub/__init__.py ruft register_package_defaults("tickerhub", runtime_path)
  → Defaults sofort in ConfigHandler Singleton geladen
App ruft load_config_file("/path/app-config.json")
  → deep-merge auf top → App-Werte überschreiben Defaults
```

**Was bleibt:**
- load_config_file(path: str) — App lädt explizit
- get_config_parameter(path, default) — Libs lesen
- get_config_for_package(package) — Libs lesen

**Was hinzukommt:**
- register_package_defaults(package_name, config_path) — Packages registrieren beim Import
- _deep_merge() — private Hilfsfunktion

**Was entfernt wird:**
- load_config_for_package() — hardcodet deployment path
- create_config_for_package() — App-Verantwortung
- create_config_from_template() — App-Verantwortung
- _create_full_package_structure() — App-Verantwortung

## Plans

- 02-01: ConfigHandler Refactor (TDD) — code + tests
- 02-02: Dokumentation — System Doc + User Doc

---
*Created: 2026-03-22*
