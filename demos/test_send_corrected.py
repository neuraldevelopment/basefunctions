"""Test email with CORRECT from address."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from basefunctions.messaging import send_email

print("=" * 70)
print("Test: Send Email mit KORREKTER From-Adresse")
print("=" * 70)

# WICHTIG: From muss die gleiche wie SMTP_USERNAME sein!
recipient = "neutro2@outlook.de"
subject = "Test Email from basefunctions - CORRECTED"
body = "Test mit korrekter From-Adresse\n\nBest regards"

try:
    print(f"\nSende Email von: id00021.102@gmail.com")
    print(f"An: {recipient}")

    # OHNE from_addr - nutzt dann default_from aus config
    send_email(to=recipient, subject=subject, body=body)

    print("\n✅ EMAIL ERFOLGREICH VERSENDET!")

except Exception as e:
    print(f"\n❌ FEHLER: {e}")
