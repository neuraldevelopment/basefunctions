# Roadmap: basefunctions

## Overview
Die Lib ist eine Sammlung von unterschiedlichen Funktionalitäten für unterschiedliche Bereiche der python Programmierung. Hier sind sämtliche Basisdienste vorhanden, die wir aktuell gebraucht haben, besonders der EventBus Mechanismus ist hier hervorzuheben, ein multithreaded Event Deploy Mechanismus mit hoher Performance.

## Current State

Bestehende Codebasis mit umfangreicher Funktionalität (v0.5.98+):

| Subpackage | Beschreibung |
|------------|--------------|
| events | EventBus — multithreaded Event-Deploy-Mechanismus |
| cli | CLI Framework mit Command-Registry, Parser, Formatter |
| config | ConfigHandler, SecretHandler |
| runtime | DeploymentManager, RuntimeFunctions, Version |
| utils | Cache, Decorators, DemoRunner, Logging, Observer, Table |
| io | FileFunctions, Serializer, OutputRedirector |
| http | HttpClient, HttpClientHandler |
| messaging | SMTP, EmailMessage |
| kpi | Collector, Registry, Exporters, Protocol |
| pandas | Accessors |

## Phasen

Phasen werden bei Bedarf mit `/paul:plan` definiert.

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| — | Noch keine Phasen definiert | — | — | — |

---
*Roadmap created: 2026-03-03*
