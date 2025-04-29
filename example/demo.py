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
