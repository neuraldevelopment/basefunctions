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

### Active (In Progress)

- [To be defined during planning]

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

## Workflow

- Phasen werden ausschließlich via /paul:add-phase aus Linear Issues angelegt (Format: NEURAL-XX-issue-titel). Nie manuell definieren.

---
*Created: 2026-03-15 16:48*
*Last updated: 2026-03-20 after Phase 1*
