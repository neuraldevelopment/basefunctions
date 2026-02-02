"""Deep debug of full SMTP send process."""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

from basefunctions.messaging import send_email
from basefunctions.messaging.email_message import EmailMessage
from basefunctions.messaging.smtp_client import SMTPClient
import smtplib

print("=" * 70)
print("DEEP SMTP DEBUG - Kompletter Ablauf")
print("=" * 70)

# 1. Manuelle Verbindung + Login
print("\n1️⃣  MANUELLE VERBINDUNG + LOGIN:")
try:
    client = SMTPClient()
    print(f"   Host: {client.host}")
    print(f"   Port: {client.port}")
    print(f"   Username: {client.username}")
    print(f"   Password: {client.password}")

    # Verbindung in Context Manager
    with SMTPClient() as smtp:
        print("   ✅ Verbunden & eingeloggt")

        # 2. Message erstellen
        print("\n2️⃣  MESSAGE ERSTELLEN:")
        msg = EmailMessage(
            to="neutro2@outlook.de",
            subject="Deep Debug Test",
            body="Test body",
            from_addr="id00021.102@gmail.com"
        )
        print(f"   From: {msg.from_addr}")
        print(f"   To: {msg.to}")
        print(f"   Subject: {msg.subject}")

        # 3. MIME-Message
        print("\n3️⃣  MIME-MESSAGE:")
        mime_msg = msg.to_mime_message()
        print(f"   From (MIME): {mime_msg['From']}")
        print(f"   To (MIME): {mime_msg['To']}")
        print(f"   Subject (MIME): {mime_msg['Subject']}")

        # 4. Senden
        print("\n4️⃣  SENDEN:")
        print("   Versuche send_message()...")
        smtp.send(msg)
        print("   ✅ EMAIL ERFOLGREICH VERSENDET!")

except Exception as e:
    print(f"\n❌ FEHLER: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
