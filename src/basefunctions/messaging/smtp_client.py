"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 SMTP client for sending emails with config/secret integration
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import logging
import smtplib
import ssl
from typing import Optional

from basefunctions.config import ConfigHandler, SecretHandler
from basefunctions.messaging.email_message import EmailMessage


# =============================================================================
# CONSTANTS
# =============================================================================
DEFAULT_PORT = 587
DEFAULT_TIMEOUT = 30
DEFAULT_USE_TLS = True
DEFAULT_USE_SSL = False


# =============================================================================
# LOGGING
# =============================================================================
logger = logging.getLogger(__name__)


# =============================================================================
# CLASS DEFINITIONS
# =============================================================================
class SMTPError(Exception):
    """Exception raised for SMTP-related errors."""

    pass


class SMTPClient:
    """
    SMTP client for sending emails with config/secret integration.

    Parameters
    ----------
    host : str, optional
        SMTP server hostname, default None (loads from config)
    port : int, optional
        SMTP server port, default None (loads from config)
    username : str, optional
        SMTP authentication username, default None (loads from secrets)
    password : str, optional
        SMTP authentication password, default None (loads from secrets)
    use_tls : bool, optional
        Use TLS encryption, default None (loads from config)
    use_ssl : bool, optional
        Use SSL encryption, default None (loads from config)
    timeout : int, optional
        Connection timeout in seconds, default None (loads from config)

    Attributes
    ----------
    host : str
        SMTP server hostname
    port : int
        SMTP server port
    username : str
        SMTP authentication username
    password : str
        SMTP authentication password
    use_tls : bool
        Use TLS encryption
    use_ssl : bool
        Use SSL encryption
    timeout : int
        Connection timeout in seconds
    default_from : str
        Default sender email address
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None,
        timeout: Optional[int] = None
    ) -> None:
        """
        Initialize SMTPClient.

        Parameters
        ----------
        host : str, optional
            SMTP server hostname, default None (loads from config)
        port : int, optional
            SMTP server port, default None (loads from config)
        username : str, optional
            SMTP authentication username, default None (loads from secrets)
        password : str, optional
            SMTP authentication password, default None (loads from secrets)
        use_tls : bool, optional
            Use TLS encryption, default None (loads from config)
        use_ssl : bool, optional
            Use SSL encryption, default None (loads from config)
        timeout : int, optional
            Connection timeout in seconds, default None (loads from config)
        """
        # Store explicit parameters
        self._explicit_host = host
        self._explicit_port = port
        self._explicit_username = username
        self._explicit_password = password
        self._explicit_use_tls = use_tls
        self._explicit_use_ssl = use_ssl
        self._explicit_timeout = timeout

        # Initialize server connection attribute
        self._server: Optional[smtplib.SMTP] = None

        # Load configuration and secrets
        self._load_config()
        self._load_secrets()

    def _load_config(self) -> None:
        """
        Load configuration from ConfigHandler.

        Loads SMTP configuration parameters from config.json.
        Explicit parameters (passed to __init__) take precedence over config values.
        """
        config_handler = ConfigHandler()

        # Load host if not explicitly set
        if self._explicit_host is not None:
            self.host = self._explicit_host
        else:
            self.host = config_handler.get_config_parameter(
                "basefunctions/messaging/smtp_host",
                "smtp.gmail.com"
            )

        # Load port if not explicitly set
        if self._explicit_port is not None:
            self.port = self._explicit_port
        else:
            self.port = config_handler.get_config_parameter(
                "basefunctions/messaging/smtp_port",
                DEFAULT_PORT
            )

        # Load use_tls if not explicitly set
        if self._explicit_use_tls is not None:
            self.use_tls = self._explicit_use_tls
        else:
            self.use_tls = config_handler.get_config_parameter(
                "basefunctions/messaging/use_tls",
                DEFAULT_USE_TLS
            )

        # Load use_ssl if not explicitly set
        if self._explicit_use_ssl is not None:
            self.use_ssl = self._explicit_use_ssl
        else:
            self.use_ssl = config_handler.get_config_parameter(
                "basefunctions/messaging/use_ssl",
                DEFAULT_USE_SSL
            )

        # Load timeout if not explicitly set
        if self._explicit_timeout is not None:
            self.timeout = self._explicit_timeout
        else:
            self.timeout = config_handler.get_config_parameter(
                "basefunctions/messaging/timeout",
                DEFAULT_TIMEOUT
            )

        # Load default_from
        self.default_from = config_handler.get_config_parameter(
            "basefunctions/messaging/default_from",
            "noreply@example.com"
        )

    def _load_secrets(self) -> None:
        """
        Load secrets from SecretHandler.

        Loads SMTP credentials from .env file.
        Explicit parameters (passed to __init__) take precedence over secret values.
        """
        secret_handler = SecretHandler()

        # Load username if not explicitly set
        if self._explicit_username is not None:
            self.username = self._explicit_username
        else:
            self.username = secret_handler.get_secret_value("SMTP_USERNAME", None)

        # Load password if not explicitly set
        if self._explicit_password is not None:
            self.password = self._explicit_password
        else:
            self.password = secret_handler.get_secret_value("SMTP_PASSWORD", None)

    def _connect(self) -> None:
        """
        Establish SMTP connection.

        Creates connection based on use_ssl:
        - use_ssl=True: smtplib.SMTP_SSL
        - use_ssl=False: smtplib.SMTP + starttls()

        Stores connection in self._server.

        Raises
        ------
        SMTPError
            On connection or TLS negotiation failure
        """
        try:
            # Create connection based on SSL setting
            if self.use_ssl:
                self._server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout)
            else:
                self._server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
                # Use STARTTLS for non-SSL connections
                self._server.starttls()

            logger.info(f"Connected to {self.host}:{self.port}")

        except TimeoutError as e:
            raise SMTPError(f"Connection timeout to {self.host}:{self.port}") from e
        except OSError as e:
            raise SMTPError(f"Cannot connect to {self.host}:{self.port}: {e}") from e
        except smtplib.SMTPException as e:
            raise SMTPError(f"SMTP error: {e}") from e

    def _login(self) -> None:
        """
        Authenticate with SMTP server.

        Raises
        ------
        SMTPError
            On authentication failure or missing configuration
        """
        # Validate server connection
        if self._server is None:
            raise SMTPError("Not connected to server")

        # Validate credentials
        if self.username is None:
            raise SMTPError("Username not configured")

        if self.password is None:
            raise SMTPError("Password not configured")

        # Attempt authentication
        try:
            self._server.login(self.username, self.password)
            logger.info(f"Authenticated as {self.username}")

        except smtplib.SMTPAuthenticationError as e:
            raise SMTPError(f"Authentication failed for {self.username}") from e
        except smtplib.SMTPException as e:
            raise SMTPError(f"SMTP error during login: {e}") from e

    def send(self, message: EmailMessage) -> None:
        """
        Send email message.

        Parameters
        ----------
        message : EmailMessage
            Message to send

        Raises
        ------
        SMTPError
            On send failure
        """
        # Validate server connection
        if self._server is None:
            raise SMTPError("Not connected to server")

        # Validate message type
        if not isinstance(message, EmailMessage):
            raise SMTPError("Message must be an EmailMessage instance")

        # Convert to MIME message
        try:
            mime_msg = message.to_mime_message()
        except Exception as e:
            raise SMTPError(f"Failed to convert message to MIME: {e}") from e

        # Send message
        try:
            self._server.send_message(mime_msg)
            logger.info(f"Email sent to {message.to}")

        except smtplib.SMTPException as e:
            raise SMTPError(f"Failed to send email: {e}") from e

    def close(self) -> None:
        """Close SMTP connection."""
        if self._server is not None:
            try:
                self._server.quit()
                logger.info("Disconnected from SMTP server")
            except Exception:
                pass
            finally:
                self._server = None

    def __enter__(self) -> "SMTPClient":
        """Context manager entry."""
        self._connect()
        self._login()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[object]
    ) -> None:
        """Context manager exit with automatic cleanup."""
        self.close()


# =============================================================================
# FUNCTION DEFINITIONS
# =============================================================================
def send_email(
    to: str,
    subject: str,
    body: str,
    from_addr: Optional[str] = None
) -> None:
    """
    Convenience function to send email.

    Uses default config/secrets. Automatically connects and closes.

    Parameters
    ----------
    to : str
        Recipient email
    subject : str
        Email subject
    body : str
        Plain text body
    from_addr : str, optional
        Sender address (default: from config)

    Raises
    ------
    SMTPError
        On connection or send failure
    EmailError
        On validation failure

    Examples
    --------
    >>> send_email(
    ...     to="user@example.com",
    ...     subject="Test",
    ...     body="Hello"
    ... )
    """
    # Send using SMTPClient context manager
    with SMTPClient() as smtp:
        # Use provided from_addr or fall back to SMTP default_from
        sender = from_addr if from_addr else smtp.default_from

        # Create email message
        msg = EmailMessage(to=to, subject=subject, body=body, from_addr=sender)

        # Send message
        smtp.send(msg)
