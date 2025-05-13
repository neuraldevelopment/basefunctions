"""
=============================================================================

 Licensed Materials, Property of neuraldevelopment , Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Example of a Corelet implementation that calculates sum from 1 to 100000

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------


# Beispiel 1: Umleiten der Ausgabe in eine Datei
@basefunctions.redirect_output("output_log.txt")
def example_function_to_file():
    print("Diese Nachricht wird in die Datei 'output_log.txt' geschrieben")
    print("Weitere Zeile für die Datei")
    return "Funktion ausgeführt"


# Beispiel 2: Umleiten der Ausgabe in einen Memory-Buffer
memory_target = basefunctions.MemoryTarget()


@basefunctions.redirect_output(memory_target)
def example_function_to_memory():
    print("Diese Nachricht wird im Speicher gespeichert")
    print("Noch eine Zeile für den Speicher")
    return 42


# Beispiel 3: Umleiten von stdout und stderr
@basefunctions.redirect_output(stdout=True, stderr=True)
def example_with_error():
    print("Normale Ausgabe")
    import sys

    sys.stderr.write("Fehler-Ausgabe\n")
    return "Fertig"


# Ausführung der Beispiele
result1 = example_function_to_file()
print(f"Ergebnis 1: {result1}")

result2 = example_function_to_memory()
print(f"Ergebnis 2: {result2}")
print(f"Gespeicherte Ausgabe: {memory_target.get_buffer()}")

result3 = example_with_error()
print(f"Ergebnis 3: {result3}")
