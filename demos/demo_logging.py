#!/usr/bin/env python3
"""
Demo: Config-Based Logging Auto-Initialization

Zeigt das neue Config-basierte Logging System.

VORHER (manuelles Setup in JEDER App):
    from basefunctions.utils.logging import get_logger, set_log_level, set_log_file
    set_log_level("INFO")
    set_log_file("/tmp/app.log")
    logger = get_logger(__name__)

JETZT (Config-basiert - ZERO Setup):
    # config.json einmal definieren
    # Dann nur noch:
    from basefunctions.utils.logging import get_logger
    logger = get_logger(__name__)
"""

import json
import tempfile
from pathlib import Path


def demo_manual_api():
    """Demo 1: Manuelle API (wie vorher)."""
    print("\n" + "=" * 80)
    print("DEMO 1: Manuelle API (Backward Compatible)")
    print("=" * 80)

    from basefunctions.utils.logging import get_logger, set_log_console, set_log_level

    # Manuelles Setup (wie vorher)
    set_log_level("INFO")
    set_log_console(enabled=True, level="INFO")

    # Logger nutzen
    logger = get_logger(__name__)
    logger.info("Manual API: Info message")
    logger.warning("Manual API: Warning message")

    print("\n✓ Manuelle API funktioniert wie vorher")


def demo_file_logging():
    """Demo 2: File-Logging mit manueller API."""
    print("\n" + "=" * 80)
    print("DEMO 2: File-Logging")
    print("=" * 80)

    from basefunctions.utils.logging import get_logger, set_log_file

    # Temporäre Log-Datei
    log_file = Path(tempfile.gettempdir()) / "demo_app.log"
    log_file.unlink(missing_ok=True)

    # File-Logging aktivieren
    set_log_file(filepath=str(log_file), level="INFO")

    # Logger nutzen
    logger = get_logger(__name__)
    logger.info("File logging: Info message")
    logger.warning("File logging: Warning message")
    logger.error("File logging: Error message")

    # Log-Datei anzeigen
    print(f"\nLog-Datei: {log_file}")
    if log_file.exists():
        print("\nInhalt:")
        print("-" * 80)
        print(log_file.read_text())
        print("-" * 80)
        log_file.unlink()

    print("\n✓ File-Logging funktioniert")


def demo_standard_log_directory():
    """Demo 3: Standard Log Directory (Best Practice)."""
    print("\n" + "=" * 80)
    print("DEMO 3: Standard Log Directory (Best Practice)")
    print("=" * 80)

    from basefunctions.utils.logging import get_logger, get_standard_log_directory, set_log_file

    # Automatische Pfad-Erkennung (Development vs. Deployment)
    log_dir = get_standard_log_directory("basefunctions")
    log_file = Path(log_dir) / "demo.log"
    log_file.unlink(missing_ok=True)

    print(f"\nAutomatisch erkanntes Log-Verzeichnis: {log_dir}")
    print(f"Log-Datei: {log_file}")

    # File-Logging aktivieren
    set_log_file(filepath=str(log_file), level="INFO")

    # Logger nutzen
    logger = get_logger(__name__)
    logger.info("Using standard log directory")
    logger.warning("Development vs. Deployment auto-detected!")

    # Log-Datei anzeigen
    if log_file.exists():
        print("\nInhalt:")
        print("-" * 80)
        print(log_file.read_text())
        print("-" * 80)
        log_file.unlink()

    print("\n✓ get_standard_log_directory() erkennt automatisch:")
    print("  - Development: <cwd>/logs")
    print("  - Deployment:  ~/.neuraldevelopment/logs/<package>/")


def demo_multi_module():
    """Demo 4: Mehrere Module loggen in EINE Datei."""
    print("\n" + "=" * 80)
    print("DEMO 4: Multi-Module Logging (ALLE Module → EINE Datei)")
    print("=" * 80)

    from basefunctions.utils.logging import get_logger, set_log_file

    # Temporäre Log-Datei
    log_file = Path(tempfile.gettempdir()) / "multi_module.log"
    log_file.unlink(missing_ok=True)

    # File-Logging aktivieren
    set_log_file(filepath=str(log_file), level="INFO")

    # Simuliere 3 verschiedene Module/Apps
    # Module 1: tickerhub
    logger1 = get_logger("tickerhub.ticker")
    logger1.info("Ticker started")
    logger1.info("Processing BTCUSDT")

    # Module 2: portfoliofunctions
    logger2 = get_logger("portfoliofunctions.portfolio")
    logger2.info("Portfolio loaded")
    logger2.info("Balance: 10,000 EUR")

    # Module 3: signalengine
    logger3 = get_logger("signalengine.engine")
    logger3.info("Engine running")
    logger3.warning("Signal threshold exceeded")

    # Log-Datei anzeigen
    print(f"\nLog-Datei: {log_file}")
    if log_file.exists():
        print("\nInhalt (ALLE 3 Module → EINE Datei):")
        print("-" * 80)
        print(log_file.read_text())
        print("-" * 80)
        log_file.unlink()

    print("\n✓ ALLE Module loggen in EINE Datei!")


def demo_config_file_example():
    """Demo 5: Config.json Beispiel."""
    print("\n" + "=" * 80)
    print("DEMO 5: Production Config.json Beispiel")
    print("=" * 80)

    # Beispiel Config
    config_example = {
        "basefunctions": {
            "log_enabled": True,
            "log_level": "INFO",
            "log_file": "/var/log/myapp/app.log",
        }
    }

    print("\nconfig.json:")
    print("-" * 80)
    print(json.dumps(config_example, indent=2))
    print("-" * 80)

    print("""
Dann in JEDER App (ZERO Setup-Code):

# tickerhub/ticker.py
from basefunctions.utils.logging import get_logger
logger = get_logger(__name__)
logger.info("Ticker started")  # → /var/log/myapp/app.log

# portfoliofunctions/portfolio.py
from basefunctions.utils.logging import get_logger
logger = get_logger(__name__)
logger.info("Portfolio loaded")  # → /var/log/myapp/app.log

# signalengine/engine.py
from basefunctions.utils.logging import get_logger
logger = get_logger(__name__)
logger.info("Engine running")  # → /var/log/myapp/app.log

✓ ALLE Apps loggen in EINE Datei!
✓ ZERO Setup-Code nötig!
✓ Nur config.json definieren!
""")


def demo_different_levels():
    """Demo 6: Verschiedene Log-Levels."""
    print("\n" + "=" * 80)
    print("DEMO 6: Log-Levels")
    print("=" * 80)

    from basefunctions.utils.logging import get_logger, set_log_console, set_log_level

    # DEBUG-Level aktivieren
    set_log_level("DEBUG")
    set_log_console(enabled=True, level="DEBUG")

    logger = get_logger(__name__)

    print("\nLog-Level: DEBUG (ALLE Nachrichten sichtbar)")
    logger.debug("DEBUG: Detaillierte Debug-Information")
    logger.info("INFO: Allgemeine Information")
    logger.warning("WARNING: Warnung")
    logger.error("ERROR: Fehler")
    logger.critical("CRITICAL: Kritischer Fehler")

    print("\n✓ Alle 5 Log-Levels funktionieren")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("CONFIG-BASIERTES LOGGING - DEMO")
    print("=" * 80)

    # Reset logging state zwischen Demos
    from basefunctions.utils.logging import _reset_logging_state

    # Demo 1: Manual API
    demo_manual_api()
    _reset_logging_state()

    # Demo 2: File Logging
    demo_file_logging()
    _reset_logging_state()

    # Demo 3: Standard Log Directory
    demo_standard_log_directory()
    _reset_logging_state()

    # Demo 4: Multi-Module
    demo_multi_module()
    _reset_logging_state()

    # Demo 5: Config Example
    demo_config_file_example()

    # Demo 6: Log Levels
    demo_different_levels()
    _reset_logging_state()

    print("\n" + "=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print("""
✓ Config-basierte Auto-Initialization
✓ 3 Parameter: log_enabled, log_level, log_file
✓ ZERO Setup-Code in Apps
✓ Silent Operation (keine Exceptions)
✓ Alle Apps loggen in EINE Datei
✓ Backward Compatible (manuelle API funktioniert weiterhin)

Config-Parameter (config.json):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
basefunctions/log_enabled  │ bool   │ false │ Master Switch
basefunctions/log_level    │ str    │ INFO  │ DEBUG/INFO/WARNING/ERROR/CRITICAL
basefunctions/log_file     │ str?   │ null  │ Pfad oder null (Console)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Vorher (Manuell):
    - Setup-Code in JEDER App
    - set_log_level(), set_log_file() Calls überall
    - Jede App muss Log-Pfad kennen

Jetzt (Config-basiert):
    - Config EINMAL definieren
    - Nur noch: logger = get_logger(__name__)
    - FERTIG!
""")


if __name__ == "__main__":
    main()
