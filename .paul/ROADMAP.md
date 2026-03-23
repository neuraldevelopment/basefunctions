# Roadmap: basefunctions

## Overview

basefunctions ist die zentrale Infrastrukturbasis aller neuraldevelopment Python-Pakete. Die Roadmap fokussiert auf Erweiterung, Stabilisierung und Qualitätssicherung der bestehenden Subpackages sowie die Einführung neuer Basisdienste nach Bedarf.

## Current Milestone

**cycle-07 — Implementation of Functions Cycle 07**
Status: 🚧 In Progress
Phases: 1 of 1 complete

## Previous Milestone

**cycle-06 — Implementation of Functions Cycle 06**
Status: ✅ Complete
Phases: 2 of 2 complete

## Phases (cycle-07)

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | neural-532-basefunctions-deploy-muss-aktuelles-package-als-source | 1/1 | ✅ Complete | 2026-03-23 |

## Phase Details (cycle-07)

### Phase 1: neural-532-basefunctions-deploy-muss-aktuelles-package-als-source

Focus: Deploy muss aktuelles Package als Source verwenden.
Plans: TBD (defined during /paul:plan)
Status: Not started

## Phases (cycle-06)

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | neural-514-basefunctions-logging | 4/4 | ✅ Complete | 2026-03-20 |
| 2 | neural-530-basefunctions-refactor-confighandler | 2/2 | ✅ Complete | 2026-03-23 |

## Phase Details (cycle-06)

### Phase 1: neural-514-basefunctions-logging

Focus: Logging audit across all subpackages — remove debug logs, add error/warning coverage at exception points.
Plans: 01-01 (cli), 02 (config+events), 03 (http+io+kpi), 04 (messaging+pandas+protocols+runtime+utils)
Result: All 2356 tests pass. Consistent logger.warning/logger.error pattern applied to all subpackages.

### Phase 2: neural-530-basefunctions-refactor-confighandler

Focus: ConfigHandler redesign — App-controlled config loading. Remove load_config_for_package(), create_config_for_package(), create_config_from_template(), _create_full_package_structure(). Keep load_config_file(), get_config_parameter(), get_config_for_package(). Remove load_config_for_package from basefunctions __init__.py exports. Clean up downstream callers (tickerhub, signalengine, etc.). Update tests and documentation.
Plans: 02-01 (ConfigHandler refactor — register_package_defaults, _deep_merge, deprecated methods removed), 02-02 (config subpackage documentation rewrite)
Result: ConfigHandler redesigned with App-controlled loading. Self-Registration Pattern established. All 2354 tests pass. Docs updated.

---
*Roadmap created: 2026-03-15 16:48*
*Milestone cycle-06 started: 2026-03-19*
*Phase 1 complete: 2026-03-20*
*Phase 2 added: 2026-03-21*
*Phase 2 complete: 2026-03-23*
*cycle-06 complete: 2026-03-23*
*cycle-07 started: 2026-03-23*
*Phase 1 added: 2026-03-23*
