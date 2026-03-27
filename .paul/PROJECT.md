# Project: basefunctions

## What This Is

basefunctions ist eine Python-Infrastrukturbibliothek, die allen neuraldevelopment-Modulen gemeinsame Basisdienste bereitstellt: Konfigurationsverwaltung, Event-Bus, Logging, HTTP-Client, Messaging, KPI-Tracking, CLI-Utilities, IO-Operationen sowie Runtime-Utilities für Development- und Deployment-Umgebungen. Das Package dient als zentrales Fundament, auf das alle anderen Pakete aufsetzen, ohne selbst von diesen abhängig zu sein.

## Core Value

Alle neuraldevelopment Python-Module haben Zugriff auf gemeinsame Basisdienste (EventBus, Config, Logging, HTTP, Messaging, KPI, IO, Runtime), ohne selbst Infrastruktur implementieren zu müssen.

## Current State

| Attribute | Value |
|-----------|-------|
| Status | Production |
| Last Updated | 2026-03-15 |

## Requirements

### Validated (Shipped)

- [x] Event-Bus (events subpackage)
- [x] Konfigurationsverwaltung (config subpackage)
- [x] Logging-Infrastruktur
- [x] HTTP-Client (http subpackage)
- [x] Messaging (messaging subpackage)
- [x] KPI-Tracking (kpi subpackage)
- [x] CLI-Utilities (cli subpackage)
- [x] IO-Operationen (io subpackage)
- [x] Runtime-Utilities inkl. Version & Deployment-Pfade (runtime subpackage)
- [x] Pandas-Utilities (pandas subpackage)
- [x] Protocols & Utils
- [x] Consistent operator-visible logging across all subpackages — Phase 1 (neural-514)
- [x] App-controlled config loading — Self-Registration Pattern, deep-merge, deprecated methods removed — Phase 2 (neural-530)
- [x] System and User documentation for config subpackage updated to new architecture — Phase 2 (neural-530)
- [x] update_packages excludes current package (venv owner) from deploy-dir install — Phase 1 (neural-532)
- [x] register_package_defaults simplified to single arg — path resolved internally, docs + demo updated — Phase 2 (neural-533)
- [x] CLI config command (ConfigCommand) — `config [package]` outputs current system configuration as JSON — Phase 3 (neural-537)

### Active (In Progress)

- (keine aktiven Tasks)

### Planned (Next)

- [To be defined during planning]

### Out of Scope

- [To be identified during planning]

## Constraints

### Technical Constraints
- Keine Abhängigkeit von anderen neuraldevelopment-Packages (basefunctions ist das Fundament)
- Python >= 3.12

### Business Constraints
- Proprietary — neuraldevelopment, Munich

## Success Criteria

- Alle abhängigen Module können basefunctions importieren und nutzen
- Zero external dependencies beyond approved third-party libs
- 80%+ Testabdeckung

## Key Decisions

| Decision | Phase | Rationale |
|----------|-------|-----------|
| logger.warning before all raises | Phase 1 | Operator-visible signal before every exception path |
| logger.error(exc_info=True) in except-re-raise blocks | Phase 1 | Full stack trace for re-raised exceptions |
| Test boundary overrides AC-1 for debug logs | Phase 1 | suppress() and decorator closures retain debug/inline calls — tests require exact patching target |
| Events duplicate imports deferred | Phase 1 | Not in scope for neural-514; tracked for future cleanup |
| register_package_defaults lädt sofort (nicht lazy) | Phase 2 | Package works without app config file; keine lazy-load Komplexität |
| load_config_for_package removed — app controls config path | Phase 2 | Hardcoded deployment path took config authority away from App |
| _deep_merge als Modul-Funktion (nicht Methode) | Phase 2 | No self needed; reusable by both load_config_file and register_package_defaults |
| register_package_defaults signature simplified to 1 arg | Phase 2 (neural-533) | Path resolved internally via get_runtime_config_path — callers no longer need to import or call it |

## Workflow

- Phasen werden ausschließlich via /paul:add-phase aus Linear Issues angelegt (Format: NEURAL-XX-issue-titel). Nie manuell definieren.

---
*Created: 2026-03-15 16:48*
*Last updated: 2026-03-27 after Phase 2 (cycle-07 complete)*
