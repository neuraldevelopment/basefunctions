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

---
*Created: 2026-03-15 16:48*
