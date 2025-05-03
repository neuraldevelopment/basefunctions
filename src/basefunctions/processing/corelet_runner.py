"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Runner script for executing corelets as standalone processes with file path support
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import importlib
import os
import pickle
import sys
from typing import Any, Dict, Optional, Type
import importlib.util
import basefunctions


# -------------------------------------------------------------
# HANDLER DISCOVERY FUNKTIONEN
# -------------------------------------------------------------
def load_module_from_file_path(file_path: str):
    """
    Lädt ein Python-Modul aus einem Dateipfad.
    """
    abs_path = os.path.abspath(file_path)
    module_name = os.path.basename(abs_path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, abs_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Kann Modul nicht laden: {abs_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def find_handler_class(module) -> Optional[Type]:
    """
    Findet eine Klasse im Modul, die CoreletHandlerInterface implementiert.
    """
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, basefunctions.CoreletHandlerInterface)
            and attr is not basefunctions.CoreletHandlerInterface
        ):
            return attr
    return None


def get_handler_for_message(message) -> basefunctions.CoreletHandlerInterface:
    """
    Zentrale Funktion zum Finden des passenden Handlers für eine Nachricht.
    """
    logger = basefunctions.get_logger(__name__)
    handler_class = None

    # 1. Versuche einen explizit angegebenen Corelet-Pfad zu verwenden
    if message.corelet_path:
        # Prüfe, ob es sich um einen Modul-Pfad oder Dateipfad handelt
        if "." in message.corelet_path and (
            "/" not in message.corelet_path and "\\" not in message.corelet_path
        ):
            # Modul-Pfad
            try:
                module = importlib.import_module(message.corelet_path)
                handler_class = find_handler_class(module)
                if handler_class:
                    logger.info(f"Handler aus Modul-Pfad geladen: {message.corelet_path}")
            except ImportError as e:
                logger.warning(f"Modul konnte nicht importiert werden: {e}")
        else:
            # Dateipfad
            # Füge .py hinzu, falls notwendig
            if not message.corelet_path.endswith(".py"):
                test_path = message.corelet_path + ".py"
                if os.path.exists(test_path):
                    message.corelet_path = test_path

            if os.path.exists(message.corelet_path):
                try:
                    module = load_module_from_file_path(message.corelet_path)
                    handler_class = find_handler_class(module)
                    if handler_class:
                        logger.info(f"Handler aus Dateipfad geladen: {message.corelet_path}")
                except Exception as e:
                    logger.warning(f"Fehler beim Laden aus Dateipfad: {e}")

    # 2. Versuche Standard-Struktur basierend auf message_type
    if not handler_class:
        try:
            module_path = f"basefunctions.processing.{message.message_type}"
            module = importlib.import_module(module_path)
            handler_class = find_handler_class(module)
            if handler_class:
                logger.info(f"Handler aus Standard-Modul geladen: {module_path}")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Standard-Modul nicht gefunden: {e}")

    # 3. Fallback auf Default-Handler
    if not handler_class:
        from basefunctions.default_handler import DefaultCoreletHandler

        handler_class = DefaultCoreletHandler
        logger.info(f"Default-Handler für Nachrichtentyp {message.message_type} verwendet")

    # Instanziiere und validiere Handler
    handler = handler_class.get_handler()
    if not isinstance(handler, basefunctions.CoreletHandlerInterface):
        raise TypeError(
            f"Handler implementiert CoreletHandlerInterface nicht: {type(handler).__name__}"
        )

    return handler


# -------------------------------------------------------------
# HAUPTFUNKTION
# -------------------------------------------------------------
def main() -> None:
    """
    Haupteinstiegspunkt für Corelet-Ausführung.
    """
    logger = basefunctions.get_logger(__name__)
    result = {"success": False, "data": None}

    try:
        # Serialisierte Nachricht von stdin lesen
        message_data = sys.stdin.buffer.read()
        message = pickle.loads(message_data)

        logger.info(
            f"Corelet-Prozess gestartet für Nachricht {message.id} (Typ: {message.message_type})"
        )

        # Handler finden und Anfrage verarbeiten
        try:
            handler = get_handler_for_message(message)
            success, data = handler.process_request(message)

            # Ergebnis vorbereiten
            result = {
                "success": success,
                "data": data,
                "message_id": message.id,
                "message_type": message.message_type,
            }

            # Erfolg/Misserfolg loggen
            if success:
                logger.info(f"Corelet-Verarbeitung erfolgreich für Nachricht {message.id}")
            else:
                logger.warning(
                    f"Corelet-Verarbeitung fehlgeschlagen für Nachricht {message.id}: {str(data) if data else 'Unbekannter Fehler'}"
                )

        except Exception as e:
            logger.error(f"Fehler bei der Handler-Verarbeitung: {str(e)}")
            result = {
                "success": False,
                "error": str(e),
                "exception_type": type(e).__name__,
                "data": None,
                "message_id": message.id if "message" in locals() else None,
                "message_type": message.message_type if "message" in locals() else None,
            }

    except Exception as e:
        logger.error(f"Ausnahme in Corelet-Ausführung: {str(e)}")
        result = {
            "success": False,
            "error": str(e),
            "exception_type": type(e).__name__,
            "data": None,
        }

    # Ergebnis über stdout zurücksenden
    try:
        serialized_result = pickle.dumps(result)
        sys.stdout.buffer.write(serialized_result)
        sys.stdout.flush()
    except Exception as e:
        # Bei Serialisierungsfehler versuche ein einfaches Fehlerobjekt zu senden
        fallback_result = {
            "success": False,
            "error": f"Ergebnis konnte nicht serialisiert werden: {str(e)}",
            "exception_type": type(e).__name__,
            "data": None,
        }
        sys.stdout.buffer.write(pickle.dumps(fallback_result))
        sys.stdout.flush()

    # Mit passendem Code beenden
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()
