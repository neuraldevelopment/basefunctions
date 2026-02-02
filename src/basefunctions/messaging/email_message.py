"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Email message builder for SMTP sending (Plain text only, Phase 1)
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import logging
import re
from email.message import EmailMessage as StdEmailMessage
from typing import Optional


# =============================================================================
# CONSTANTS
# =============================================================================
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


# =============================================================================
# LOGGING
# =============================================================================
logger = logging.getLogger(__name__)


# =============================================================================
# CLASS DEFINITIONS
# =============================================================================
class EmailError(Exception):
    """Exception raised for email-related errors."""

    pass


class EmailMessage:
    """
    Email message builder for SMTP sending.

    Parameters
    ----------
    to : str
        Recipient email address
    subject : str
        Email subject line
    body : str
        Email body text (plain text)
    from_addr : str, optional
        Sender email address, default None

    Attributes
    ----------
    to : str
        Recipient email address
    subject : str
        Email subject line
    body : str
        Email body text
    from_addr : str or None
        Sender email address
    """

    def __init__(
        self,
        to: str,
        subject: str,
        body: str,
        from_addr: Optional[str] = None,
    ) -> None:
        """
        Initialize EmailMessage.

        Parameters
        ----------
        to : str
            Recipient email address
        subject : str
            Email subject line
        body : str
            Email body text (plain text)
        from_addr : str, optional
            Sender email address, default None
        """
        # Validate required fields
        if not to:
            raise EmailError("'to' is required")
        if not subject:
            raise EmailError("'subject' is required")
        if not body:
            raise EmailError("'body' is required")

        # Validate email format
        self._validate_email(to)

        self.to = to
        self.subject = subject
        self.body = body
        self.from_addr = from_addr

    @staticmethod
    def _validate_email(email: str) -> bool:
        """
        Validate email address format.

        Parameters
        ----------
        email : str
            Email address to validate

        Returns
        -------
        bool
            True if valid

        Raises
        ------
        EmailError
            If email format is invalid
        """
        if not email:
            raise EmailError(f"Invalid email format: {email}")

        pattern = re.compile(EMAIL_REGEX)
        if not pattern.match(email):
            raise EmailError(f"Invalid email format: {email}")

        return True

    def to_mime_message(self) -> StdEmailMessage:
        """
        Convert EmailMessage to standard library EmailMessage (MIME format).

        Returns
        -------
        StdEmailMessage
            Standard library email message ready for SMTP sending

        Notes
        -----
        Uses 'noreply@example.com' as default From address if not specified.
        """
        mime_msg = StdEmailMessage()
        mime_msg["To"] = self.to
        mime_msg["Subject"] = self.subject
        mime_msg["From"] = self.from_addr if self.from_addr else "noreply@example.com"
        mime_msg.set_content(self.body)

        return mime_msg
