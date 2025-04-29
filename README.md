# Introduction

basefunctions ist eine einfache Bibliothek mit oft benötigten Basisfunktionen. Sie bietet u.a. Funktionen für Dateiverarbeitung und eine ThreadPool-Implementierung mit automatischem Retry- und Timeout-Management.

## Getting Started

Folgende Funktionalitäten sind enthalten:

- `database` – SQL-Hilfsfunktionen
- `filefunctions` – Datei-Hilfsfunktionen
- `threadpool` – ThreadPool-Klasse mit Nachrichtensystem

## Installing

```bash
pip install basefunctions
```

## Usage

### Verwendung der Datei-Hilfsfunktionen

```python
import basefunctions as bf

bf.get_current_directory()
/Users/neutro2/
```

### Verwendung der ThreadPool-Klasse

Nachfolgend ein erweitertes Beispiel zur Nutzung des ThreadPools:

```python
import time
import basefunctions

# Beispielklassen, die ThreadPoolRequestInterface implementieren

class A(basefunctions.ThreadPoolRequestInterface):
    def process_request(self, thread_local_data, input_queue, message):
        print(f"A: callable called with item: {message.content}")
        time.sleep(2)
        return False, None

class B(basefunctions.ThreadPoolRequestInterface):
    def process_request(self, thread_local_data, input_queue, message):
        print(f"B: callable called with item: {message.content}")
        time.sleep(5)
        return False, None

class C(basefunctions.ThreadPoolRequestInterface):
    def process_request(self, thread_local_data, input_queue, message):
        print(f"C: callable called with item: {message.content}")
        time.sleep(5)
        return False, None

# Registrierung der Handler im ThreadPool
tp = basefunctions.ThreadPool()

tp.register_message_handler("1", A())
tp.register_message_handler("2", B())
tp.register_message_handler("3", C())

# Erstellen von Nachrichten
msg1 = basefunctions.ThreadPoolMessage(message_type="1", retry_max=3, timeout=3, content="1")
msg2 = basefunctions.ThreadPoolMessage(message_type="2", retry_max=3, timeout=2, content="2")
msg3 = basefunctions.ThreadPoolMessage(message_type="3", retry_max=2, timeout=2, content="3")

# Senden der Nachrichten
print("starting")
tp.get_input_queue().put(msg1)
tp.get_input_queue().put(msg2)
tp.get_input_queue().put(msg3)

# Warten bis alle Aufgaben abgeschlossen sind
tp.wait_for_all()
print("finished")
```

### Hinweise

- Die `retry_max`- und `timeout`-Parameter steuern, wie oft ein Task bei Fehlern erneut versucht wird und wie lange er maximal laufen darf.
- Wenn ein Task erfolgreich abgeschlossen wird (`success=True`), wird nicht weiter neu gestartet.
- Wenn eine TimeoutException auftritt, wird der Task automatisch unterbrochen und neu gestartet.
- Es können beliebig viele verschiedene Aufgaben gleichzeitig vom ThreadPool verarbeitet werden.

## Project Homepage

<https://github.com/neuraldevelopment/basefunctions>

## Contribute

Fehler gefunden oder neue Funktionen gewünscht? E-Mail an <neutro2@outlook.de>.