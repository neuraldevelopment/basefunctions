"""Check loaded credentials in plain text."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from basefunctions.config import SecretHandler, ConfigHandler

print("=" * 70)
print("CREDENTIALS CHECK")
print("=" * 70)

secret_handler = SecretHandler()
config_handler = ConfigHandler()

username = secret_handler.get_secret_value("SMTP_USERNAME", None)
password = secret_handler.get_secret_value("SMTP_PASSWORD", None)

smtp_host = config_handler.get_config_parameter(
    "basefunctions/messaging/smtp_host",
    "smtp.gmail.com"
)

print("\n📧 SMTP CONFIGURATION:")
print(f"Host: {smtp_host}")
print(f"Username: {username}")
print(f"Password (PLAINTEXT): {password}")
print(f"Password Length: {len(password) if password else 0}")

if password:
    print(f"\nPassword Charaktere:")
    for i, char in enumerate(password):
        print(f"  [{i}]: '{char}' (ASCII: {ord(char)})")
