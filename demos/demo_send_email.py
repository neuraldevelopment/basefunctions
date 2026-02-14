"""
=============================================================================
Licensed Materials, Property of neuraldevelopment, Munich
Project : basefunctions
Copyright (c) by neuraldevelopment
All rights reserved.
Description:
Demo: Sending emails using basefunctions.messaging
Log:
v1.0.0 : Initial implementation
=============================================================================
"""

from basefunctions.messaging import EmailMessage, SMTPClient, send_email


def main() -> None:
    """Demonstrate email sending with basefunctions.messaging."""

    print("=" * 70)
    print("EMAIL SENDING DEMO")
    print("=" * 70)

    # =========================================================================
    # EXAMPLE 1: Simple email sending using convenience function
    # =========================================================================
    print("\n[Example 1] Using send_email() convenience function")
    print("-" * 70)
    print("This is the simplest way to send an email.")
    print("Uses configuration from config.json and secrets from .env")
    print()

    try:
        send_email(
            to="recipient@example.com",
            subject="Hello from basefunctions",
            body="This is a test email sent using basefunctions.messaging"
        )
        print("✓ Email sent successfully")
    except Exception as e:
        print(f"✗ Error: {e}")

    # =========================================================================
    # EXAMPLE 2: Email sending with custom sender address
    # =========================================================================
    print("\n[Example 2] Using send_email() with custom from address")
    print("-" * 70)
    print("Specify a custom sender address if needed.")
    print()

    try:
        send_email(
            to="recipient@example.com",
            subject="Custom sender example",
            body="This email was sent with a custom from address",
            from_addr="custom@example.com"
        )
        print("✓ Email sent successfully")
    except Exception as e:
        print(f"✗ Error: {e}")

    # =========================================================================
    # EXAMPLE 3: Advanced usage with SMTPClient for more control
    # =========================================================================
    print("\n[Example 3] Using SMTPClient for advanced control")
    print("-" * 70)
    print("For more control over the SMTP connection, use SMTPClient directly.")
    print()

    try:
        with SMTPClient() as smtp:
            message = EmailMessage(
                to="recipient@example.com",
                subject="Advanced SMTP example",
                body="This email was sent using SMTPClient directly",
                from_addr="sender@example.com"
            )
            smtp.send(message)
            print("✓ Email sent successfully")
    except Exception as e:
        print(f"✗ Error: {e}")

    # =========================================================================
    # EXAMPLE 4: Sending multiple emails with SMTPClient
    # =========================================================================
    print("\n[Example 4] Sending multiple emails with SMTPClient")
    print("-" * 70)
    print("Reuse the connection for multiple emails (more efficient).")
    print()

    recipients = [
        "user1@example.com",
        "user2@example.com",
        "user3@example.com",
    ]

    try:
        with SMTPClient() as smtp:
            for recipient in recipients:
                message = EmailMessage(
                    to=recipient,
                    subject="Batch email",
                    body=f"Hello {recipient}!",
                    from_addr="sender@example.com"
                )
                smtp.send(message)
                print(f"✓ Email sent to {recipient}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
