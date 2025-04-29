"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Example for using the URLDOWNLOADER ThreadPool handler to download heise.de

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import basefunctions

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
if __name__ == "__main__":
    # ThreadPool initialisieren
    pool = basefunctions.ThreadPool()

    # URLDOWNLOADER Handler registrieren
    pool.register_message_handler("urldownloader", basefunctions.url_downloader)

    # Message bauen
    message = basefunctions.ThreadPoolMessage(
        message_type="urldownloader",
        content="https://heise.de",
        timeout=10,
    )

    # Message in Input-Queue geben
    pool.get_input_queue().put(message)

    # Warten bis abgeschlossen
    pool.get_input_queue().join()

    # Ergebnisse einsammeln
    results = pool.get_results_from_output_queue()
    for result in results:
        print("=== SUCCESS ===" if result.success else "=== ERROR ===")
        print(result.data if result.success else f"{result.error}")
