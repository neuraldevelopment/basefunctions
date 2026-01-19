# CHANGELOG

## [v0.5.53] - 2026-01-19

**Purpose:** Central table format configuration for consistent formatting across package

**Changes:**
- Added table_formatter.py (v1.0) in utils subpackage with get_table_format() function
- Uses ConfigHandler to read "basefunctions/table_format" from config.json (default "grid")
- Added "table_format": "grid" entry to config/config.json
- Refactored exporters.py (v1.3 → v1.4): Removed tablefmt parameter from print_kpi_table()
- Refactored demo_runner.py (v2.0 → v2.1): Replace hardcoded "grid" with get_table_format()
- Centralized table format configuration enables consistent formatting across all tabulate calls

**Breaking Changes:**
- print_kpi_table() signature changed: Removed tablefmt parameter (now reads from config)
- Migration: Remove tablefmt argument from print_kpi_table() calls - format now configured in config.json

**Technical Details:**
- KISSS compliance: Simple function, no overengineering
- Type hints mandatory: get_table_format() -> str
- NumPy docstring with Brief, Returns, Examples
- Import order: stdlib, third-party, project (3 groups)
- File headers with version logs updated
- Imports consolidated at file top in demo_runner.py (Standard Library, Third-party, Project modules)

## [v0.5.52] - 2026-01-18

**Purpose:** Add print_kpi_table function for formatted console KPI output with grouping and filtering

**Changes:**
- Added print_kpi_table() function in kpi/exporters.py (v1.3)
- Groups KPIs by category.package (first two path segments) and prints separate table per group
- Wildcard filtering support with fnmatch (OR-logic: match if ANY pattern matches)
- Right-aligned values with tabulate (numalign="right")
- Auto-detect int/float formatting: int(value) if value == int(value), else f"{value:.{decimals}f}"
- Optional unit column (include_units parameter, default True)
- Section headers: "## {Category} KPIs - {Package}"
- Table format customizable via tablefmt parameter (default "grid")
- Exported in basefunctions.kpi public API (__init__.py v1.2)
- Added fnmatch import to exporters.py
- Reuses existing _flatten_dict() helper for nested dict flattening

**Breaking Changes:**
- None

**Technical Details:**
- Input validation: decimals >= 0 (ValueError if negative)
- Empty kpis dict → prints message and returns early
- No matches after filtering → prints message and returns early
- Missing "value" key in KPIValue → defensive handling with backward compatibility for plain values
- Sort keys alphabetically within each group (sort_keys parameter, default True)
- Unit display: unit string if present, "-" for None
- Blank line between group tables for readability

## [v0.5.51] - 2026-01-17

**Purpose:** KPIValue format support in exporters with optional unit suffixes

**Changes:**
- Added _format_unit_suffix() helper function in kpi/exporters.py (v1.2) to format units as column name suffixes
- Updated _flatten_dict() with KPIValue detection logic - extracts numeric value from {"value": float, "unit": Optional[str]} format
- Added include_units_in_columns parameter to export_to_dataframe(), export_by_category(), export_business_technical_split()
- Default behavior unchanged (include_units_in_columns=False) - backward compatible
- Column name examples: "balance" (default) vs "balance_USD" (with units), "%" → "_pct" special handling
- Updated all docstrings with KPIValue format examples and unit suffix behavior

**Breaking Changes:**
- None - Fully backward compatible with default parameter

**Technical Details:**
- KPIValue format detection: Check for "value" and "unit" keys in dict
- Recursive flattening with include_units_in_columns propagation
- Plain values (backward compatibility) still supported
- File versioning: v1.1 → v1.2

## [v0.5.51] - 2026-01-17

**Purpose:** Add optional unit metadata to KPI values for display formatting

**Changes:**
- Added KPIValue TypedDict in kpi/utils.py (v1.1) with value/unit structure
- Updated group_kpis_by_name() docstring with unit examples and clarified KPIValue format
- KPIValue exported from basefunctions.kpi public API
- Updated kpi/__init__.py (v1.1) to export KPIValue
- Updated tests/test_kpi_utils.py (v1.1) to use KPIValue format - all 10 existing tests updated + 1 new test added

**Breaking Changes:**
- KPI values now expect dict format: {"value": float, "unit": Optional[str]}
- Previous plain float/int format no longer supported for proper unit tracking

**Technical Details:**
- TypedDict for type safety with value (float) and unit (Optional[str])
- Backward compatible function logic - group_kpis_by_name() works with Any values
- Documentation updated with unit usage examples
- Test coverage: 100% (27 statements, 11 tests, all passing)

## [v0.5.50] - 2026-01-17

**Purpose:** Add KPI grouping utility for nested structure transformation

**Changes:**
- Added group_kpis_by_name() function in kpi/utils.py (v1.0)
- Transform flat KPI dict with dot-separated names into nested structure
- Preserves insertion order (Python 3.7+ dict behavior)
- Handles single-level keys (stay flat) and multi-level nesting
- Exported in basefunctions.kpi public API
- Added demo_kpi_grouping.py (v1.0) showcasing 5 scenarios: Real-world portfolio KPIs, order preservation, mixed nesting, deep nesting (3+ levels), edge cases

**Breaking Changes:**
- None

**Technical Details:**
- Simple split + nested dict building algorithm
- Minimal KISSS implementation to pass test contract
- Demo includes visual BEFORE/AFTER comparison with json.dumps() pretty-printing

## [v0.5.47] - 2026-01-15

**Änderungen:**
- Added category filtering to KPICollector (collect_by_category method for business/technical prefix filtering)
- Improved _filter_by_prefix() docstring with examples and clarified recursive filtering logic
- Extended exporters.py (v1.1) mit category-based Export-Funktionen: export_by_category(), export_business_technical_split(), _filter_history_by_prefix()

## [v0.5.46] - 2026-01-15

**Purpose:** Binary filelist tracking for automatic wrapper cleanup in deployment system

**Changes:**
- Added binary filelist tracking in deployment_manager.py (v1.12)
- New helper methods: _get_filelist_path(), _read_filelist(), _write_filelist(), _cleanup_old_wrappers()
- Modified _deploy_bin_tools() to track deployed binaries and cleanup obsolete wrappers
- Filelist stored in ~/.neuraldevelopment/packages/<package>/.deploy/bin-filelist.txt
- Format: binary_name|timestamp_iso8601 (one per line)
- Automatic cleanup: Removed binaries from Development → Wrappers automatically deleted
- Added KPIRegistry (registry.py v1.0) - Module-level dict for KPI provider discovery
- Registry functions: register(), get_all_providers(), clear()
- Updated kpi/__init__.py to export registry functions

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
