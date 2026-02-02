# Messaging - User Documentation

**Package:** basefunctions
**Subpackage:** messaging
**Version:** 0.5.78
**Purpose:** Send emails via SMTP with configuration and secret management

---

## Overview

The messaging subpackage provides email sending functionality using SMTP. It integrates with ConfigHandler and SecretHandler for secure credential management and supports various SMTP providers like Gmail, Outlook, and Yahoo.

**Key Features:**
- Plain text email sending via SMTP
- Automatic credential loading from SecretHandler
- Configuration-based SMTP settings
- Support for TLS and SSL connections
- Context manager for automatic connection cleanup
- Provider-agnostic (Gmail, Outlook, Yahoo, custom SMTP)

**Common Use Cases:**
- Sending notification emails
- User registration confirmations
- Password reset emails
- Alert and monitoring notifications
- Batch email sending

---

## Public APIs

### send_email()

**Purpose:** Convenience function to send a single email with minimal setup

```python
from basefunctions.messaging import send_email

send_email(
    to="recipient@example.com",
    subject="Hello",
    body="This is a test email"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `to` | str | - | Recipient email address |
| `subject` | str | - | Email subject line |
| `body` | str | - | Plain text message body |
| `from_addr` | str | None | Sender address (uses config default if None) |

**Returns:**
- **Type:** None
- **Description:** No return value. Raises exceptions on failure.

**Raises:**
- `SMTPError`: Connection, authentication, or send failure
- `EmailError`: Invalid email format or validation failure

**Examples:**

```python
from basefunctions.messaging import send_email

# Basic usage
send_email(
    to="customer@example.com",
    subject="Order Confirmation",
    body="Your order #12345 has been confirmed."
)

# With custom sender
send_email(
    to="customer@example.com",
    subject="Welcome!",
    body="Welcome to our service",
    from_addr="noreply@mycompany.com"
)
```

**Best For:**
- Single email sending
- Simple notification workflows
- Quick testing
- One-off messages

---

### EmailMessage

**Purpose:** Email message builder for SMTP sending

```python
from basefunctions.messaging import EmailMessage

msg = EmailMessage(
    to="recipient@example.com",
    subject="Test",
    body="Hello World",
    from_addr="sender@example.com"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `to` | str | - | Recipient email address |
| `subject` | str | - | Email subject line |
| `body` | str | - | Plain text message body |
| `from_addr` | str | None | Sender email address |

**Returns:**
- **Type:** EmailMessage
- **Description:** Message object ready for SMTP sending

**Raises:**
- `EmailError`: If required fields are missing or email format is invalid

**Examples:**

```python
from basefunctions.messaging import EmailMessage, SMTPClient

# Create message
msg = EmailMessage(
    to="recipient@example.com",
    subject="Test",
    body="Hello World",
    from_addr="sender@example.com"
)

# Send via SMTPClient
with SMTPClient() as smtp:
    smtp.send(msg)
```

**Best For:**
- Constructing messages before sending
- Batch email preparation
- Message validation before sending
- Reusable message templates

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `to_mime_message()` | - | `StdEmailMessage` | Convert to MIME format for SMTP |

---

### SMTPClient

**Purpose:** SMTP client for sending emails with configuration and secret integration

```python
from basefunctions.messaging import SMTPClient

# Using config/secrets (recommended)
with SMTPClient() as smtp:
    smtp.send(msg)

# With explicit parameters
with SMTPClient(
    host="smtp.gmail.com",
    port=587,
    username="user@gmail.com",
    password="app_password"
) as smtp:
    smtp.send(msg)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | None | SMTP server hostname (loads from config) |
| `port` | int | None | SMTP server port (loads from config) |
| `username` | str | None | SMTP username (loads from secrets) |
| `password` | str | None | SMTP password (loads from secrets) |
| `use_tls` | bool | None | Use TLS encryption (loads from config) |
| `use_ssl` | bool | None | Use SSL encryption (loads from config) |
| `timeout` | int | None | Connection timeout in seconds (loads from config) |

**Returns:**
- **Type:** SMTPClient
- **Description:** SMTP client instance

**Raises:**
- `SMTPError`: Connection, authentication, or send failure

**Examples:**

```python
from basefunctions.messaging import SMTPClient, EmailMessage

# Context manager (recommended)
with SMTPClient() as smtp:
    msg = EmailMessage(
        to="user@example.com",
        subject="Test",
        body="Hello"
    )
    smtp.send(msg)

# Manual connection (not recommended)
smtp = SMTPClient()
smtp._connect()
smtp._login()
smtp.send(msg)
smtp.close()

# Batch sending
with SMTPClient() as smtp:
    for recipient in recipients:
        msg = EmailMessage(
            to=recipient,
            subject="Newsletter",
            body="Monthly update..."
        )
        smtp.send(msg)
```

**Best For:**
- Sending multiple emails with one connection
- Advanced SMTP configurations
- Custom provider settings
- Production email workflows

**Key Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `send()` | `message: EmailMessage` | None | Send email message |
| `close()` | - | None | Close SMTP connection |
| `__enter__()` | - | SMTPClient | Context manager entry (auto-connect) |
| `__exit__()` | - | None | Context manager exit (auto-close) |

**Context Manager Pattern:**
Always prefer using SMTPClient as a context manager to ensure proper connection cleanup:

```python
# GOOD
with SMTPClient() as smtp:
    smtp.send(msg)

# AVOID
smtp = SMTPClient()
smtp.send(msg)  # Connection not established
```

---

## Configuration Guide

### Basic Configuration

Create configuration in `~/.neuraldevelopment/config.json` or `./config/basefunctions.json`:

```json
{
  "basefunctions": {
    "messaging": {
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "use_tls": true,
      "use_ssl": false,
      "timeout": 30,
      "default_from": "noreply@example.com"
    }
  }
}
```

### Configuration Reference

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `smtp_host` | str | No | smtp.gmail.com | SMTP server hostname |
| `smtp_port` | int | No | 587 | SMTP server port |
| `use_tls` | bool | No | true | Use TLS encryption (STARTTLS) |
| `use_ssl` | bool | No | false | Use SSL encryption (SMTP_SSL) |
| `timeout` | int | No | 30 | Connection timeout in seconds |
| `default_from` | str | No | noreply@example.com | Default sender email address |

### Secrets Configuration

Create file `~/.env` with SMTP credentials:

```
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Security Notes:**
- Never hardcode credentials in your code
- Use environment variables or SecretHandler for credentials
- For Gmail with 2FA, use app-specific passwords
- Keep `.env` file out of version control

### Provider-Specific Configurations

#### Gmail

```json
{
  "basefunctions": {
    "messaging": {
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "use_tls": true,
      "use_ssl": false
    }
  }
}
```

**Gmail Setup:**
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Create an app password for "Mail"
4. Use the app password in `.env` as `SMTP_PASSWORD`

#### Outlook / Office 365

```json
{
  "basefunctions": {
    "messaging": {
      "smtp_host": "smtp.office365.com",
      "smtp_port": 587,
      "use_tls": true,
      "use_ssl": false
    }
  }
}
```

#### Yahoo

```json
{
  "basefunctions": {
    "messaging": {
      "smtp_host": "smtp.mail.yahoo.com",
      "smtp_port": 587,
      "use_tls": true,
      "use_ssl": false
    }
  }
}
```

#### Custom SMTP Server

```json
{
  "basefunctions": {
    "messaging": {
      "smtp_host": "mail.yourcompany.com",
      "smtp_port": 465,
      "use_tls": false,
      "use_ssl": true
    }
  }
}
```

---

## Usage Examples

### Basic Usage (Most Common)

**Scenario:** Send a simple notification email

```python
from basefunctions.messaging import send_email

# Step 1: Send email using convenience function
send_email(
    to="customer@example.com",
    subject="Order Confirmation",
    body="Your order #12345 has been confirmed and will ship soon."
)

# Step 2: Check logs for confirmation
# INFO: Email sent to customer@example.com
```

---

### Batch Email Sending

**Scenario:** Send multiple emails efficiently with a single connection

```python
from basefunctions.messaging import SMTPClient, EmailMessage

# List of recipients
recipients = [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
]

# Send to all recipients
with SMTPClient() as smtp:
    for recipient in recipients:
        msg = EmailMessage(
            to=recipient,
            subject="Monthly Newsletter",
            body="This month's updates and news..."
        )
        smtp.send(msg)

print(f"Sent {len(recipients)} emails")
```

---

### Custom Sender Address

**Scenario:** Send email from a specific sender address

```python
from basefunctions.messaging import send_email

send_email(
    to="customer@example.com",
    subject="Support Ticket Update",
    body="Your support ticket #789 has been resolved.",
    from_addr="support@mycompany.com"
)
```

---

### Error Handling

**Scenario:** Handle SMTP errors gracefully

```python
from basefunctions.messaging import send_email, SMTPError, EmailError

try:
    send_email(
        to="customer@example.com",
        subject="Test",
        body="Hello"
    )
    print("Email sent successfully")

except SMTPError as e:
    # SMTP connection, authentication, or send error
    print(f"SMTP Error: {e}")
    # Log error, retry, or alert admin

except EmailError as e:
    # Email validation error (invalid format, missing fields)
    print(f"Email Error: {e}")
    # Fix email format and retry
```

---

### Integration with ConfigHandler

**Scenario:** Override configuration for specific use case

```python
from basefunctions.messaging import SMTPClient, EmailMessage

# Use custom SMTP server for this operation
with SMTPClient(
    host="mail.specialprovider.com",
    port=465,
    username="special@example.com",
    password="special_password",
    use_ssl=True
) as smtp:
    msg = EmailMessage(
        to="vip@example.com",
        subject="VIP Message",
        body="Special message for VIP customer"
    )
    smtp.send(msg)
```

---

## Error Handling

### Common Errors

**Error 1: Authentication Failed**

```python
# WRONG - Invalid credentials
with SMTPClient() as smtp:
    smtp.send(msg)
# SMTPError: Authentication failed for user@gmail.com
```

**Solution:**
```python
# CORRECT - Check .env file
# ~/.env should contain:
# SMTP_USERNAME=user@gmail.com
# SMTP_PASSWORD=correct_app_password
```

**What Went Wrong:** The username or password in `.env` is incorrect. For Gmail, ensure you're using an app-specific password, not your regular password.

---

**Error 2: Invalid Email Format**

```python
# WRONG
msg = EmailMessage(
    to="invalid-email",  # Missing @ and domain
    subject="Test",
    body="Hello"
)
# EmailError: Invalid email format: invalid-email
```

**Solution:**
```python
# CORRECT
msg = EmailMessage(
    to="valid@example.com",  # Proper email format
    subject="Test",
    body="Hello"
)
```

**What Went Wrong:** Email address must follow format: `local@domain.tld`

---

**Error 3: Connection Timeout**

```python
# WRONG - Incorrect host or port
config = {
    "smtp_host": "wrong.smtp.com",
    "smtp_port": 9999
}
# SMTPError: Connection timeout to wrong.smtp.com:9999
```

**Solution:**
```python
# CORRECT - Use proper SMTP server settings
config = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587
}
```

**What Went Wrong:** SMTP host or port is incorrect. Verify provider documentation for correct settings.

---

### Error Recovery

```python
from basefunctions.messaging import send_email, SMTPError, EmailError
import logging

logger = logging.getLogger(__name__)

def send_with_retry(to: str, subject: str, body: str, max_retries: int = 3):
    """Send email with retry logic"""
    for attempt in range(max_retries):
        try:
            send_email(to=to, subject=subject, body=body)
            logger.info(f"Email sent successfully on attempt {attempt + 1}")
            return True

        except SMTPError as e:
            logger.warning(f"SMTP error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to send email after {max_retries} attempts")
                raise

        except EmailError as e:
            # Don't retry validation errors
            logger.error(f"Email validation error: {e}")
            raise

    return False
```

---

## Best Practices

### Best Practice 1: Use Context Manager

**Why:** Ensures SMTP connection is properly closed even if errors occur

```python
# GOOD
with SMTPClient() as smtp:
    smtp.send(msg)
# Connection automatically closed
```

```python
# AVOID
smtp = SMTPClient()
smtp._connect()
smtp.send(msg)
smtp.close()  # Might not run if error occurs
```

---

### Best Practice 2: Keep Credentials in .env

**Why:** Prevents credential leaks and enables environment-specific configuration

```python
# GOOD
with SMTPClient() as smtp:
    # Loads credentials from .env
    smtp.send(msg)
```

```python
# AVOID
smtp = SMTPClient(
    username="hardcoded@gmail.com",
    password="hardcoded_password"  # Security risk!
)
```

---

### Best Practice 3: Validate Emails Before Sending

**Why:** EmailMessage validates on construction, catching errors early

```python
# GOOD
try:
    msg = EmailMessage(
        to=user_email,  # Validated here
        subject="Welcome",
        body="Hello"
    )
    with SMTPClient() as smtp:
        smtp.send(msg)
except EmailError as e:
    print(f"Invalid email: {e}")
```

```python
# AVOID
# No validation until send attempt
with SMTPClient() as smtp:
    smtp._server.sendmail(...)  # Might fail late
```

---

### Best Practice 4: Reuse Connection for Batch Sending

**Why:** More efficient than creating new connection for each email

```python
# GOOD - Single connection
with SMTPClient() as smtp:
    for recipient in recipients:
        msg = EmailMessage(to=recipient, subject="...", body="...")
        smtp.send(msg)
```

```python
# AVOID - Multiple connections
for recipient in recipients:
    send_email(to=recipient, subject="...", body="...")
    # Creates new connection each time
```

---

## Choosing the Right Approach

### When to Use send_email()

Use `send_email()` when:
- Sending a single email
- Quick testing or prototyping
- Simple notification workflows
- Minimal configuration needed

```python
# Example: Simple notification
send_email(
    to="admin@example.com",
    subject="Server Alert",
    body="CPU usage exceeded 90%"
)
```

**Pros:**
- Simplest API
- Automatic connection management
- One-line email sending

**Cons:**
- Creates new connection for each call
- Less efficient for batch sending

---

### When to Use EmailMessage + SMTPClient

Use `EmailMessage` + `SMTPClient` when:
- Sending multiple emails
- Need connection reuse
- Custom SMTP configuration
- Production workflows

```python
# Example: Batch sending
with SMTPClient() as smtp:
    for user in users:
        msg = EmailMessage(
            to=user.email,
            subject="Weekly Update",
            body=f"Hello {user.name}..."
        )
        smtp.send(msg)
```

**Pros:**
- Efficient batch sending
- Explicit connection control
- Better error handling
- Reusable connections

**Cons:**
- More verbose
- Requires context manager

---

### When to Use Custom SMTP Parameters

Use explicit parameters when:
- Testing different providers
- Environment-specific overrides
- Multiple SMTP accounts
- Special configurations

```python
# Example: Testing provider
with SMTPClient(
    host="smtp.testprovider.com",
    port=2525,
    username="test@example.com",
    password="test_password"
) as smtp:
    smtp.send(msg)
```

**Pros:**
- Full control over settings
- No config file changes needed
- Easy testing

**Cons:**
- Bypasses configuration system
- Can lead to credential hardcoding if not careful

---

## FAQ

**Q: What email formats are supported?**

A: Currently only plain text emails. HTML emails and attachments will be added in future phases.

**Q: How do I send to multiple recipients?**

A: Loop through recipients and send individual emails. CC/BCC support is planned for future releases.

**Q: Why is my Gmail authentication failing?**

A: Gmail requires app-specific passwords when 2FA is enabled. Regular passwords won't work. Create an app password at https://myaccount.google.com/apppasswords

**Q: Can I use this without ConfigHandler?**

A: Yes. Pass all parameters explicitly to `SMTPClient()`:
```python
SMTPClient(host="smtp.gmail.com", port=587, username="...", password="...")
```

**Q: How do I debug SMTP connection issues?**

A: Enable logging to see detailed connection information:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

**Q: Is TLS or SSL more secure?**

A: Both are secure. TLS (STARTTLS on port 587) is the modern standard. SSL (SMTP_SSL on port 465) is the legacy approach. Use TLS unless your provider requires SSL.

---

## See Also

**Related Subpackages:**
- `config` (`docs/basefunctions/config.md`) - Configuration and secret management
- `events` (`docs/basefunctions/events.md`) - Event system for message notifications

**System Documentation:**
- `~/.claude/_docs/python/basefunctions.md` - Internal architecture details

**External Resources:**
- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229) - Official Gmail SMTP documentation
- [Python smtplib](https://docs.python.org/3/library/smtplib.html) - Python SMTP library documentation

---

## Quick Reference

### Imports

```python
# Convenience function
from basefunctions.messaging import send_email

# All public exports
from basefunctions.messaging import (
    EmailMessage,
    EmailError,
    SMTPClient,
    SMTPError,
    send_email
)
```

### Quick Start

```python
# Step 1: Configure credentials in ~/.env
# SMTP_USERNAME=your_email@gmail.com
# SMTP_PASSWORD=your_app_password

# Step 2: Send email
from basefunctions.messaging import send_email

send_email(
    to="recipient@example.com",
    subject="Hello",
    body="This is a test"
)
```

### Cheat Sheet

| Task | Code |
|------|------|
| Send single email | `send_email(to="...", subject="...", body="...")` |
| Create message | `EmailMessage(to="...", subject="...", body="...")` |
| Send with custom settings | `SMTPClient(host="...", port=...)` |
| Batch sending | `with SMTPClient() as smtp: ...` |
| Error handling | `try/except SMTPError/EmailError` |

---

**Document Version:** 0.5.78
**Last Updated:** 2026-02-01
**Subpackage Version:** 1.0.0
