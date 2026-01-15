# CHANGELOG

## [v0.5.46] - 2026-01-15

**Purpose:** Binary filelist tracking for automatic wrapper cleanup in deployment system

**Changes:**
- Added binary filelist tracking in deployment_manager.py (v1.12)
- New helper methods: _get_filelist_path(), _read_filelist(), _write_filelist(), _cleanup_old_wrappers()
- Modified _deploy_bin_tools() to track deployed binaries and cleanup obsolete wrappers
- Filelist stored in ~/.neuraldevelopment/packages/<package>/.deploy/bin-filelist.txt
- Format: binary_name|timestamp_iso8601 (one per line)
- Automatic cleanup: Removed binaries from Development → Wrappers automatically deleted

**Breaking Changes:**
- None - Functionality is purely additive

## [v0.5.45] - 2026-01-15

**Änderungen:**
- Neues KPI-System mit Protocol-basierter Architektur (basefunctions.kpi subpackage)
- KPIProvider Protocol für standardisierte KPI-Bereitstellung mit Subprovider-Support
- KPICollector für rekursive KPI-Sammlung mit History-Management
- export_to_dataframe() für DataFrame-Export mit Flattening-Logic (dot notation)
- Vollständige Type Hints und NumPy Docstrings

## [v0.5.43] - 2026-01-13

**Änderungen:**
- Lazy Loading Pattern für CLI Command-Gruppen implementiert
- Neue Methode register_command_group_lazy() in CLIApplication
- Cache-basiertes Import-System mit importlib für On-Demand Handler-Loading
- Optimierte Startup-Zeit durch verzögertes Laden nicht benötigter Command-Gruppen
- Fixed CLI Lazy Loading Root-Level Command Group collision bug (changed _lazy_groups from dict[str, str] to dict[str, list[str]])

## [v0.5.42] - 2026-01-13

**Änderungen:**
- Added comprehensive exception handling in cli_application.py (run() and _execute_command() methods)
- Fixed ContextManager.get_prompt() to preserve insertion order (removed sorted()) in context_manager.py

---

## [v0.5.40] - 2025-12-30

**Purpose:** Framework-Style Migration - Standard conformity for subpackage structure

**Changes:**
- Created __init__.py for subpackages: config, events, http, io, pandas, utils
- Added subpackage imports to basefunctions/__init__.py
- Added subpackages to __all__ export list
- Enables Framework-Style usage: `basefunctions.cli.BaseCommand`, `basefunctions.io.serialize()`, etc.

**Breaking Changes:**
- None - Full backward compatibility maintained
- Both import styles now supported:
  - Flat (existing): `from basefunctions import BaseCommand`
  - Hierarchical (new): `from basefunctions.cli import BaseCommand`

---

## [Unreleased]

**Added:**
- Added py.typed marker for PEP 561 compliance - Type checkers now recognize bundled type hints

---

## [v1.0.0] - 2025-12-29

**🔴 BREAKING CHANGES:**

- **Migration tqdm → alive-progress 3.3.0**
  - ❌ `TqdmProgressTracker` entfernt
  - ❌ Dependency `tqdm>=4.67` entfernt
  - ❌ File `src/basefunctions/cli/progress_tracker.py` gelöscht
  - ✅ `AliveProgressTracker` neu implementiert
  - ✅ Dependency `alive-progress>=3.3.0` hinzugefügt

**Architecture Changes:**

- Clean Architecture: `utils/progress_tracker.py` ist Single Source of Truth
- `cli/__init__.py` importiert direkt aus `utils/` (ZERO Redundanz)
- Alle Import-Pfade funktionieren weiterhin:
  - `from basefunctions import AliveProgressTracker`
  - `from basefunctions.cli import AliveProgressTracker`
  - `from basefunctions.utils import AliveProgressTracker`

**Migration Guide:**

```python
# OLD (entfernt)
from basefunctions import TqdmProgressTracker
tracker = TqdmProgressTracker(total=100, desc="Processing")

# NEW
from basefunctions import AliveProgressTracker
tracker = AliveProgressTracker(total=100, desc="Processing")

# API bleibt identisch:
with tracker:
    for i in range(100):
        tracker.progress(1)
```

**Files Changed:**

- `src/basefunctions/utils/progress_tracker.py` - Rewrite mit AliveProgressTracker
- `src/basefunctions/cli/progress_tracker.py` - DELETED
- `src/basefunctions/cli/__init__.py` - Direct import aus utils
- `src/basefunctions/__init__.py` - Export AliveProgressTracker
- `tests/cli/test_progress_tracker.py` - Tests updated
- `demos/tqdm_progress.py` → `demos/progress_demo.py` - Renamed & updated
- `pyproject.toml` - Dependency updated

---

## [v0.5.37] - 2025-12-23

**Änderungen:**
- Neues Modul protocols.py mit MetricsSource Protocol für standardisierte KPI-Bereitstellung
- MetricsSource Protocol in basefunctions.__init__.py exportiert (korrekt aus utils.protocols)
