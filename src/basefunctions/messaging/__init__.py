"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Package for email/SMTP functionality
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

from basefunctions.messaging.email_message import EmailError, EmailMessage
from basefunctions.messaging.smtp_client import SMTPClient, SMTPError, send_email

__all__ = [
    "EmailMessage",
    "EmailError",
    "SMTPClient",
    "SMTPError",
    "send_email",
]
