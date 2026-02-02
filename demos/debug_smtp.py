"""Debug SMTP connection issues."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from basefunctions.messaging.smtp_client import SMTPClient
import smtplib

def debug_smtp() -> None:
    """Debug SMTP connection step by step."""
    print("=" * 70)
    print("SMTP DEBUG")
    print("=" * 70)

    # Load SMTP config
    smtp_client = SMTPClient()

    print("\n1. LOADED CONFIGURATION:")
    print(f"   Host: {smtp_client.host}")
    print(f"   Port: {smtp_client.port}")
    print(f"   Username: {smtp_client.username}")
    print(f"   Password: {'***' if smtp_client.password else 'NOT SET'}")
    print(f"   Use TLS: {smtp_client.use_tls}")
    print(f"   Use SSL: {smtp_client.use_ssl}")

    # Check if credentials are set
    if not smtp_client.username or not smtp_client.password:
        print("\n❌ FEHLER: Username oder Password nicht geladen!")
        print("   Prüfe ~/.env Datei auf SMTP_USERNAME und SMTP_PASSWORD")
        return

    print("\n2. VERBINDUNG WIRD HERGESTELLT...")
    try:
        server = smtplib.SMTP(smtp_client.host, smtp_client.port, timeout=10)
        print("   ✅ Verbindung erfolgreich")

        print("\n3. STARTTLS WIRD AKTIVIERT...")
        server.starttls()
        print("   ✅ STARTTLS aktiv")

        print("\n4. AUTHENTIFIZIERUNG...")
        print(f"   Versuche Login mit: {smtp_client.username}")
        server.login(smtp_client.username, smtp_client.password)
        print("   ✅ AUTHENTIFIZIERUNG ERFOLGREICH!")

        server.quit()

    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ AUTHENTIFIZIERUNG FEHLGESCHLAGEN:")
        print(f"      {e}")
        print("\n   LÖSUNGEN:")
        print("   1. App-Passwort muss NICHT benannt werden")
        print("   2. Aber: Gmail benötigt 2FA aktiviert!")
        print("   3. Prüfe: https://myaccount.google.com/apppasswords")
        print("   4. Stelle sicher, dass das App-Passwort:")
        print("      - Für 'Mail' und 'Windows Computer' erstellt wurde")
        print("      - 16 Zeichen lang ist (keine Leerzeichen)")
        print("      - Aktuell gültig ist (nicht abgelaufen)")
        return
    except Exception as e:
        print(f"   ❌ FEHLER: {e}")
        return

    print("\n" + "=" * 70)
    print("✅ ALLE TESTS ERFOLGREICH - SMTP FUNKTIONIERT!")
    print("=" * 70)


if __name__ == "__main__":
    debug_smtp()
