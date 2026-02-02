"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Demo script: Send a test email via basefunctions.messaging module

 This script demonstrates how to send a simple email using the
 basefunctions.messaging module.

 Prerequisites:
 - Configure SMTP settings in ~/.neuraldevelopment/config.json
 - Set SMTP_USERNAME and SMTP_PASSWORD in ~/.env file
 - For Outlook: Use your email password or app-specific password

 Usage:
     python demos/send_test_email.py
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

import sys
from pathlib import Path

# Add src to path to import basefunctions
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from basefunctions.messaging import EmailError, SMTPError, send_email
from basefunctions.messaging.smtp_client import SMTPClient


def print_smtp_parameters() -> None:
    """Print SMTP configuration parameters in a table."""
    smtp_client = SMTPClient()

    print("\n" + "=" * 70)
    print("SMTP CONFIGURATION PARAMETERS")
    print("=" * 70)

    # Define parameters with their values
    parameters = [
        ("Host", smtp_client.host),
        ("Port", str(smtp_client.port)),
        ("Username", smtp_client.username or "N/A"),
        ("Password", "***" if smtp_client.password else "N/A"),
        ("Use TLS", str(smtp_client.use_tls)),
        ("Use SSL", str(smtp_client.use_ssl)),
        ("Timeout (s)", str(smtp_client.timeout)),
        ("Default From", smtp_client.default_from),
    ]

    # Calculate column widths
    max_key_len = max(len(key) for key, _ in parameters)
    max_val_len = max(len(str(val)) for _, val in parameters)

    # Print table header
    print(f"\n{'Parameter':<{max_key_len}}  │  {'Value':<{max_val_len}}")
    print("-" * (max_key_len + max_val_len + 5))

    # Print table rows
    for key, val in parameters:
        print(f"{key:<{max_key_len}}  │  {str(val):<{max_val_len}}")

    print("=" * 70)


def main() -> None:
    """Send a test email."""
    print("=" * 70)
    print("Demo: Send Test Email via basefunctions.messaging")
    print("=" * 70)

    # Get SMTP client for sender info
    smtp_client = SMTPClient()

    recipient = "neutro2@outlook.de"
    sender = smtp_client.default_from
    subject = "Test Email from basefunctions.messaging"
    body = """Hello!

This is a test email sent from basefunctions.messaging demo script.

Features:
- Uses ConfigHandler for SMTP settings
- Uses SecretHandler for credentials
- Simple and clean API

Best regards,
basefunctions.messaging Demo
"""

    # Show SMTP parameters
    print_smtp_parameters()

    # Show email addresses
    print("\nEMAIL ADDRESSES")
    print("=" * 70)
    print(f"From:  {sender}")
    print(f"To:    {recipient}")
    print(f"Subject: {subject}")
    print("-" * 70)

    # Send 100 emails
    total_emails = 1
    successful = 0
    failed = 0

    print(f"\nSending {total_emails} emails...\n")

    for i in range(1, total_emails + 1):
        try:
            send_email(to=recipient, subject=subject, body=body)
            successful += 1
            print(f"[{i:3d}/{total_emails}] ✅ Email sent successfully")

        except EmailError as e:
            failed += 1
            print(f"[{i:3d}/{total_emails}] ❌ Email validation error: {e}")
        except SMTPError as e:
            failed += 1
            print(f"[{i:3d}/{total_emails}] ❌ SMTP error: {e}")

    print("-" * 70)
    print(f"\nRESULTS:")
    print(f"  Total:      {total_emails}")
    print(f"  Successful: {successful}")
    print(f"  Failed:     {failed}")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
