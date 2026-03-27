#!/usr/bin/env python3
"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Demo: App-controlled configuration system with Self-Registration Pattern.
 Shows how apps consume ConfigHandler: packages register defaults at import,
 apps load their config once at startup, all code reads via get_config_parameter.
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import json
import logging
import tempfile
from pathlib import Path

from basefunctions import ConfigHandler

# =============================================================================
# CONSTANTS
# =============================================================================
SEPARATOR = "=" * 80
DEMO_PACKAGE = "basefunctions"

# =============================================================================
# LOGGING
# =============================================================================
logger = logging.getLogger(__name__)


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================


def demo_step1_defaults_at_import() -> None:
    """Show package defaults available immediately after import.

    basefunctions.__init__ already called register_package_defaults("basefunctions")
    when this script imported basefunctions above — no explicit call needed here.
    This mirrors exactly what any downstream package does in its own __init__.py.
    """
    print(f"\n{SEPARATOR}")
    print("STEP 1: Package defaults auto-registered at import time")
    print(SEPARATOR)
    print()
    print("In any package __init__.py:")
    print('  from basefunctions import ConfigHandler')
    print('  ConfigHandler().register_package_defaults("mypackage")')
    print()
    print("basefunctions already called this for itself at import time.")
    print("Defaults are immediately available — no app config file needed.")
    print()

    defaults = ConfigHandler().get_config_for_package(DEMO_PACKAGE)
    print(f"State of ConfigHandler after 'import basefunctions':")
    print(json.dumps({DEMO_PACKAGE: defaults}, indent=2))
    print()
    print("✓ Defaults registered. Package works even without an app config file.")


def demo_step2_load_app_config(app_config_path: Path) -> None:
    """Load an app config that overrides specific defaults.

    Parameters
    ----------
    app_config_path : Path
        Path to the app config JSON file to load
    """
    print(f"\n{SEPARATOR}")
    print("STEP 2: App loads its config once at startup")
    print(SEPARATOR)
    print()
    print("App startup code:")
    print(f'  ConfigHandler().load_config_file("{app_config_path}")')
    print()

    app_config = json.loads(app_config_path.read_text(encoding="utf-8"))
    print("App config.json content:")
    print(json.dumps(app_config, indent=2))
    print()

    ConfigHandler().load_config_file(str(app_config_path))
    print("✓ App config deep-merged over package defaults.")


def demo_step3_deep_merge_result() -> None:
    """Show the merged config state after app config was loaded."""
    print(f"\n{SEPARATOR}")
    print("STEP 3: Deep-merge result — app wins, untouched defaults preserved")
    print(SEPARATOR)
    print()

    merged = ConfigHandler().get_config_for_package(DEMO_PACKAGE)
    print("ConfigHandler().get_config_for_package('basefunctions'):")
    print(json.dumps(merged, indent=2))
    print()
    print("✓ table_format overridden: 'grid' → 'rounded'  (set by app config)")
    print("✓ messaging.smtp_host preserved from package defaults  (not in app config)")
    print("✓ logging.level added as new key  (was absent in defaults)")


def demo_step4_read_params() -> None:
    """Show reading individual parameters via get_config_parameter."""
    print(f"\n{SEPARATOR}")
    print("STEP 4: Reading parameters anywhere in code")
    print(SEPARATOR)
    print()

    # Overridden value
    table_format = ConfigHandler().get_config_parameter(f"{DEMO_PACKAGE}/table_format")
    print(f"  get_config_parameter('{DEMO_PACKAGE}/table_format')")
    print(f"  → '{table_format}'   (overridden by app config)")
    print()

    # Preserved default (nested key)
    smtp_host = ConfigHandler().get_config_parameter(f"{DEMO_PACKAGE}/messaging/smtp_host")
    print(f"  get_config_parameter('{DEMO_PACKAGE}/messaging/smtp_host')")
    print(f"  → '{smtp_host}'   (preserved from package defaults)")
    print()

    # New key added by app config
    log_level = ConfigHandler().get_config_parameter(f"{DEMO_PACKAGE}/logging/level")
    print(f"  get_config_parameter('{DEMO_PACKAGE}/logging/level')")
    print(f"  → '{log_level}'   (added by app config)")
    print()

    # Missing key — default_value returned
    timeout = ConfigHandler().get_config_parameter(f"{DEMO_PACKAGE}/api/timeout", 30)
    print(f"  get_config_parameter('{DEMO_PACKAGE}/api/timeout', 30)")
    print(f"  → {timeout}   (key absent — default_value returned)")
    print()
    print("✓ All reads via get_config_parameter. No key errors. default_value is the fallback.")


def main() -> None:
    """Run all config system demo steps."""
    print(f"\n{SEPARATOR}")
    print("basefunctions — Config System Demo")
    print("App-controlled config with Self-Registration Pattern")
    print(SEPARATOR)

    # Step 1: defaults already registered by 'import basefunctions' at module level
    demo_step1_defaults_at_import()

    # Step 2: create a temporary app config and load it
    app_config = {
        DEMO_PACKAGE: {
            "table_format": "rounded",  # overrides package default "grid"
            "logging": {
                "level": "INFO"  # new key — not present in package defaults
            }
        }
    }
    config_file = Path(tempfile.gettempdir()) / "demo_basefunctions_config.json"
    config_file.write_text(json.dumps(app_config, indent=2), encoding="utf-8")

    demo_step2_load_app_config(config_file)
    demo_step3_deep_merge_result()
    demo_step4_read_params()

    config_file.unlink(missing_ok=True)

    print(f"\n{SEPARATOR}")
    print("SUMMARY — Self-Registration Pattern")
    print(SEPARATOR)
    print("""
  Package __init__.py (once per package):
    ConfigHandler().register_package_defaults("mypackage")
    → Loads config/config.json from deploy dir. Silent if file missing.

  App startup (once per process):
    ConfigHandler().load_config_file("/path/to/app-config.json")
    → Deep-merges over all registered defaults. Raises on file/JSON error.

  Anywhere in code:
    ConfigHandler().get_config_parameter("mypackage/section/key", default)
    ConfigHandler().get_config_for_package("mypackage")
    → Reads from the merged singleton. Thread-safe.

  Deep-merge rules:
    ✓ App config overrides matching package defaults
    ✓ Untouched package defaults remain intact
    ✓ New keys in app config are added
    ✓ Nested dicts merged recursively — no whole-section clobbers
""")


if __name__ == "__main__":
    main()
