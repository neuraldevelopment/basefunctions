# CHANGELOG

## [v0.5.69] - 2026-01-25

**Purpose:** Change default sort_keys behavior to preserve insertion order in KPI table output

**Changes:**
- Changed default sort_keys parameter in print_kpi_table() from True to False (src/basefunctions/kpi/exporters.py, v1.13 → v1.14)
- Docstring updated to reflect new default (line 751: "default False")
- Preserves KPI insertion order by default for more intuitive output
- Users can still explicitly set sort_keys=True for alphabetical sorting

**Breaking Changes:**
- None - Default behavior change only, existing code with sort_keys=True still works identically

**Technical Details:**
- KISSS compliance: Minimal change (1 parameter default + docstring)
- Logic unchanged: if sort_keys block (line 817) remains identical
- File version: v1.13 → v1.14

## [v0.5.68] - 2026-01-25

**Purpose:** Add global logging enable/disable functionality

**Changes:**
- Added enable_logging(enabled: bool) to utils/logging.py (v3.1 → v3.2)
- Global ON/OFF switch for all logging output across all modules
- When disabled: Sets root logger to CRITICAL+1 (effectively silent)
- When enabled: Sets root logger to DEBUG (allows all configured loggers to work)
- Does not affect individual logger configurations (setup_logger, configure_module_logging)
- Full NumPy docstring with Parameters, Examples
- Type hints: (enabled: bool) -> None
- Exported in basefunctions public API (__init__.py)
- Added get_standard_log_directory() to utils/logging.py (v3.0 → v3.1)
- Automatic environment detection (development vs deployment) via get_runtime_log_path()
- Development: <cwd>/logs, Deployment: ~/.neuraldevelopment/logs/<package>/
- Optional directory creation via ensure_exists parameter (default: True)

**Breaking Changes:**
- None

**Technical Details:**
- KISSS compliance: Simple root logger level manipulation (4 lines of logic)
- enabled=True → root.setLevel(logging.DEBUG)
- enabled=False → root.setLevel(logging.CRITICAL + 1)
- Works with existing setup_logger(), configure_module_logging() without modification
- Use case: Temporarily disable logging in performance-critical sections
- Example: enable_logging(False) → ... → enable_logging(True)

## [v0.5.67] - 2026-01-24

**Purpose:** HTTP request performance optimization with connection pooling

**Changes:**
- Added connection pooling to HttpClientHandler via requests.Session singleton
- Module-level _SESSION with HTTPAdapter (pool_connections=100, pool_maxsize=100)
- Replaced requests.request() with _SESSION.request() for 10x performance improvement
- 252 requests: ~26s → ~3-5s (connection reuse instead of new connection per request)
- Thread-safe implementation (Session is thread-safe for concurrent reading)

**Breaking Changes:**
- None - Pure performance optimization, no API changes

**Technical Details:**
- Added HTTPAdapter import from requests.adapters
- Constants: _POOL_CONNECTIONS=100, _POOL_MAXSIZE=100
- Session mounted for both http:// and https://
- File version: v1.2 → v1.3
- KISSS compliance: Module-level singleton (simplest solution, no config needed)

## [v0.5.63] - 2026-01-22

**Purpose:** Fixed-width table formatting with exact width enforcement

**Changes:**
- print_kpi_table() now enforces FIXED width (not maximum) via max_table_width parameter
- Added column_widths parameter to _build_table_rows_with_sections()
- Implemented padding with ljust()/rjust() to force exact column widths
- Column distribution: 60% for KPI names, 40% for values
- Corrected overhead calculation: -7 for grid borders, -4 for tabulate's extra spacing
- Headers padded to match column widths, forcing tabulate to respect fixed width

**Breaking Changes:**
- None - max_table_width now enforces fixed width instead of maximum (previous behavior was incorrect)

**Technical Details:**
- available_width = max_table_width - 7 - 4 (accounts for tabulate adding 2 spaces per column)
- kpi_width = int(available_width * 0.60)
- value_width = available_width - kpi_width
- Padding: kpi_str.ljust(kpi_width), value_str.rjust(value_width)
- Headers also padded to force tabulate width compliance
- File version: v1.12 → v1.13

## [v0.5.62] - 2026-01-22

**Purpose:** Correct column alignment - KPI names left, values right

**Changes:**
- Replaced `stralign="right"` with `colalign=("left", "right")` in print_kpi_table()
- KPI names now left-aligned (with proper indentation for sub-items)
- Values remain right-aligned for perfect decimal point alignment
- Removed numalign/stralign parameters (colalign handles both)

**Breaking Changes:**
- None - Visual improvement only

**Technical Details:**
- tabulate parameter: colalign=("left", "right")
- First column (KPI): left-aligned
- Second column (Value): right-aligned
- File version: v1.11 → v1.12

## [v0.5.61] - 2026-01-22

**Purpose:** Proper right-alignment for all values in KPI tables

**Changes:**
- Added `stralign="right"` to tabulate() call in print_kpi_table()
- Ensures all values (including strings with units) are right-aligned
- Previously only pure numbers were right-aligned (numalign="right")
- Now values like "0.60 %", "1000.00 EUR", "-0.13" all align properly

**Breaking Changes:**
- None - Visual improvement only

**Technical Details:**
- tabulate parameters: numalign="right" + stralign="right"
- Affects Value column: decimal points and units align consistently
- File version: v1.10 → v1.11

## [v0.5.60] - 2026-01-22

**Purpose:** Consistent decimal formatting for all numeric values

**Changes:**
- Removed int-detection in _format_value_with_unit()
- All numeric values now always formatted with specified decimal places (default: 2)
- Ensures consistent right-alignment with decimal points aligned
- Examples: "5.00" instead of "5", "1000.00 EUR" instead of "1000 EUR"

**Breaking Changes:**
- Integer values now display with decimals: "42" → "42.00"
- May affect visual parsing where users expected integer-only display

**Technical Details:**
- Removed: `if value == int(value): formatted = str(int(value))`
- Now: Always `formatted = f"{value:.{decimals}f}"`
- File version: v1.9 → v1.10

## [v0.5.59] - 2026-01-22

**Purpose:** Configurable table width for print_kpi_table()

**Changes:**
- Added `max_table_width` parameter to print_kpi_table() (default: 80 characters)
- Table columns automatically sized proportionally (60% KPI, 40% Value) to fit within width limit
- Replaces hardcoded maxcolwidths=[60, None] with dynamic calculation
- Table overhead calculation: 6 chars for borders and spacing (| space | space |)

**Breaking Changes:**
- None - New optional parameter with sensible default
- Previous unlimited Value column width now constrained to 40% of available width

**Technical Details:**
- Calculation: available_width = max_table_width - 6
- KPI column: 60% of available width
- Value column: 40% of available width
- File version: v1.8 → v1.9

## [v0.5.58] - 2026-01-22

**Purpose:** Use central table format configuration for consistent formatting

**Changes:**
- Modified print_kpi_table() to use get_table_format() from utils.table_formatter
- Changed table_format parameter from hardcoded default "fancy_grid" to Optional[str] = None
- If None, reads format from config (basefunctions/table_format, default "grid")
- Ensures consistent table formatting across entire package

**Breaking Changes:**
- Default table format changes from "fancy_grid" to "grid" (config default)
- Users can override via config or table_format parameter

**Technical Details:**
- Import: basefunctions.utils.table_formatter.get_table_format
- File version: v1.7 → v1.8

## [v0.5.57] - 2026-01-22

**Purpose:** Currency override functionality for print_kpi_table()

**Changes:**
- Added `currency` parameter to print_kpi_table() (default: "EUR")
- All known currency codes (USD, GBP, CHF, JPY, etc.) automatically replaced with specified currency
- Added CURRENCY_CODES constant with 24 supported currency codes
- Updated _format_value_with_unit() to replace currencies based on CURRENCY_CODES set
- Updated _build_table_rows_with_sections() to pass currency parameter through
- Example: "1000.00 USD" → "1000.00 EUR" (with default), or "1000.00 CHF" (with currency="CHF")

**Breaking Changes:**
- None - New optional parameter with default "EUR"

**Technical Details:**
- CURRENCY_CODES includes: USD, EUR, GBP, CHF, JPY, CNY, CAD, AUD, SEK, NOK, DKK, PLN, CZK, HUF, RUB, INR, BRL, MXN, ZAR, KRW, SGD, HKD, NZD, TRY
- Non-currency units (%, days, -, etc.) remain unchanged
- File version: v1.6 → v1.7

## [v0.5.56] - 2026-01-21

**Purpose:** Professional single-table-per-package KPI display format with integrated units

**Changes:**
- Refactored print_kpi_table() in kpi/exporters.py (v1.5 → v1.6)
- Changed grouping from 3-level (category.package.subgroup) to 2-level (package-only)
- Subgroups now displayed as UPPERCASE section headers within table (e.g., "ACTIVITY", "RETURNS")
- Metrics indented with 2 spaces under subgroup headers (e.g., "  win_rate")
- Units integrated into Value column (e.g., "0.75 %", "1000.00 USD" instead of separate Unit column)
- Empty separator rows between subgroup sections for readability
- Single professional table per package with metric count in header (e.g., "Portfoliofunctions KPIs - 5 Metrics")
- Default table format changed to "fancy_grid" (modern, professional)
- Metric names show only last segment (e.g., "win_rate" NOT "activity.win_rate")
- Fixed decimals default to 2 (no auto-detect)
- Added 6 new helper functions: _extract_metric_name(), _extract_subgroup_name(), _format_value_with_unit(), _organize_kpis_by_package_subgroup(), _build_table_rows_with_sections(), _format_package_name()

**Breaking Changes:**
- ❌ Parameter `include_units` REMOVED - Units now always integrated into Value column
- ❌ Output format changed: 3-level grouping → 2-level grouping (package-only)
- ❌ Section headers removed: "## Category KPIs - Package - Subgroup" → Single table with UPPERCASE subgroup headers
- ❌ Metric display changed: Full path (e.g., "activity.win_rate") → Last segment only (e.g., "win_rate")
- **Migration Path:** Remove `include_units` parameter from print_kpi_table() calls - Format is now automatic

**Technical Details:**
- KISSS compliance: Simple helpers, clear separation of concerns
- Type hints mandatory: All functions fully typed
- NumPy docstrings: Brief, Parameters, Returns, Examples
- Backward compatible: filter_patterns, sort_keys, decimals still work
- New parameter: table_format (default "fancy_grid") for professional formatting
- File version incremented v1.5 → v1.6

## [v0.5.55] - 2026-01-21

**Purpose:** 3-level KPI sub-grouping for improved KPI table structure

**Changes:**
- Updated print_kpi_table() in kpi/exporters.py (v1.4 → v1.5)
- Changed grouping from 2-level (category.package) to 3-level (category.package.subgroup)
- Section headers now display: "## Category KPIs - Package - Subgroup"
- Table headers use subgroup name as primary label when available
- Backward compatible with 2-segment KPIs (graceful fallback to legacy grouping)
- Example: "business.portfoliofunctions.activity.win_rate" → Group: "Business.Portfoliofunctions.Activity", Display: "Activity"

**Breaking Changes:**
- None - Fully backward compatible with 2-level KPI names

**Technical Details:**
- KISSS compliance: Simple string manipulation with split() and conditional logic
- Graceful degradation: 3-segment → 3-level group, 2-segment → 2-level group, 1-segment → 1-level group
- Updated docstring to reflect 3-level grouping behavior
- File version incremented v1.4 → v1.5

## [v0.5.54] - 2026-01-20

**Purpose:** Remove MarketDataProvider protocol (YAGNI refactoring)

**Changes:**
- Deleted `src/basefunctions/protocols/market_data.py` (MarketDataProvider protocol)
- Removed MarketDataProvider import from `protocols/__init__.py`
- Removed MarketDataProvider from public API exports in root `__init__.py`
- Protocol was never reused - only implemented by MarketDataManager in backtesterfunctions
- Violates YAGNI principle: Removes unused abstraction layer

**Breaking Changes:**
- ❌ `from basefunctions import MarketDataProvider` no longer available
- ❌ `from basefunctions.protocols import MarketDataProvider` no longer available
- **Migration Path:** Use concrete DataService class from backtesterfunctions instead
- Public API now exports only 2 protocols: KPIProvider, MetricsSource

**Impact:**
- All 1750 tests passing ✅
- 258 LOC removed (eliminated unused protocol)
- Cleaner, simpler API surface
- KISSS compliance: Removed overengineered abstraction

## [v0.5.53] - 2026-01-19

**Purpose:** Implement MarketDataProvider protocol and consolidate all protocols to centralized protocols/ directory

**Changes:**
- Created new `src/basefunctions/protocols/` subpackage for structural typing protocols
- Added market_data.py (v1.0) with MarketDataProvider protocol (runtime_checkable)
- Defined interface methods: get_current_prices(), get_prices_at_bar()
- Defined properties: current_bar (int), current_date (pd.Timestamp)
- Protocol enables portfolio functions to work independently from concrete data providers
- Added __init__.py (v1.0) in protocols subpackage with MarketDataProvider export
- **MIGRATION:** Consolidated existing protocols to centralized directory:
  - Migrated MetricsSource from `utils/protocols.py` → `protocols/metrics_source.py` (v1.0)
  - Migrated KPIProvider from `kpi/protocol.py` → `protocols/kpi_provider.py` (v1.0)
  - Updated protocols/__init__.py to export all 3 protocols (KPIProvider, MarketDataProvider, MetricsSource)
- Updated all internal imports:
  - kpi/collector.py: Changed import from `kpi.protocol` to `protocols.KPIProvider`
  - kpi/registry.py: Changed import from `kpi.protocol` to `protocols.KPIProvider`
- Maintained backward compatibility via re-exports:
  - `from basefunctions.utils import MetricsSource` still works (re-exported in utils/__init__.py)
  - `from basefunctions.kpi import KPIProvider` still works (re-exported in kpi/__init__.py)
- Updated root __init__.py: Consolidated protocol imports, exports all 3 protocols in public API
- All methods include complete NumPy docstrings with Brief, Parameters, Returns, Notes, Examples
- All parameters and returns have type hints

**Breaking Changes:**
- None (full backward compatibility maintained)

**Technical Details:**
- KISSS compliance: Simple protocols, no overengineering
- Type hints mandatory: All methods and properties fully typed
- NumPy docstrings: Brief, Parameters, Returns, Raises, Notes, Examples
- Import order: stdlib, third-party, project (3 groups)
- File headers with version logs in all new files
- Protocols support duck-typing with IDE/type-checker support
- Centralized directory enables: single source of truth, consistent evolution, clear organization
- Old files (`utils/protocols.py`, `kpi/protocol.py`) can be deleted after testing
- No external dependencies beyond pandas (already in basefunctions)

## [v0.5.52] - 2026-01-18

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
