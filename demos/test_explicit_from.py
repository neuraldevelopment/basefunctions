"""Test email mit expliziter from_addr."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from basefunctions.messaging import send_email

print("=" * 70)
print("Test: Send Email mit EXPLIZITER from_addr")
print("=" * 70)

try:
    print("\nSende Email...")
    send_email(
        to="neutro2@outlook.de",
        subject="Test mit expliziter From-Adresse",
        body="Das sollte jetzt funktionieren!\n\nBest regards",
        from_addr="id00021.102@gmail.com"  # Explizit!
    )
    print("\n✅ EMAIL ERFOLGREICH VERSENDET!")

except Exception as e:
    print(f"\n❌ FEHLER: {e}")
