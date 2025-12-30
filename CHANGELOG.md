# CHANGELOG

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
