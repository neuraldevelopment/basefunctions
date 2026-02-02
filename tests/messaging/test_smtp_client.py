"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for SMTPClient - email sending with config/secret integration
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from basefunctions.messaging.email_message import EmailMessage
from basefunctions.messaging.smtp_client import SMTPClient, SMTPError


# =============================================================================
# TEST CONFIG LOADING
# =============================================================================
def test_smtp_client_init_loads_config_from_config_handler():
    """
    Test that SMTPClient loads config from ConfigHandler when no explicit params.

    Verifies config loading works and values are correctly assigned to instance.
    """
    # Arrange
    mock_config_handler = MagicMock()
    mock_config_handler.get_config_parameter.side_effect = [
        "smtp.test.com",      # smtp_host
        465,                  # smtp_port
        False,                # use_tls
        True,                 # use_ssl
        60,                   # timeout
        "test@example.com"    # default_from
    ]

    mock_secret_handler = MagicMock()
    mock_secret_handler.get_secret_value.side_effect = [None, None]

    # Act
    with patch('basefunctions.messaging.smtp_client.ConfigHandler', return_value=mock_config_handler):
        with patch('basefunctions.messaging.smtp_client.SecretHandler', return_value=mock_secret_handler):
            client = SMTPClient()

    # Assert
    assert client.host == "smtp.test.com"
    assert client.port == 465
    assert client.use_tls is False
    assert client.use_ssl is True
    assert client.timeout == 60
    assert client.default_from == "test@example.com"


def test_smtp_client_init_explicit_params_override_config():
    """
    Test that explicit parameters override config values.

    Verifies explicit params take precedence over ConfigHandler values.
    """
    # Arrange
    explicit_host = "custom.smtp.com"
    explicit_port = 2525

    # Act
    client = SMTPClient(host=explicit_host, port=explicit_port)

    # Assert
    assert client.host == "custom.smtp.com"
    assert client.port == 2525


# =============================================================================
# Test Suite 3: Secret Loading
# =============================================================================
def test_smtp_client_init_loads_secrets_from_secret_handler():
    """
    Test that SMTPClient loads secrets from SecretHandler when no explicit params.

    Verifies secret loading works and values are correctly assigned to instance.
    """
    # Arrange
    mock_config_handler = MagicMock()
    mock_config_handler.get_config_parameter.side_effect = [
        "smtp.gmail.com",
        587,
        True,
        False,
        30,
        "noreply@example.com"
    ]

    mock_secret_handler = MagicMock()
    mock_secret_handler.get_secret_value.side_effect = [
        "user@gmail.com",    # SMTP_USERNAME
        "app_password"       # SMTP_PASSWORD
    ]

    # Act
    with patch('basefunctions.messaging.smtp_client.ConfigHandler', return_value=mock_config_handler):
        with patch('basefunctions.messaging.smtp_client.SecretHandler', return_value=mock_secret_handler):
            client = SMTPClient()

    # Assert
    assert client.username == "user@gmail.com"
    assert client.password == "app_password"


# =============================================================================
# Test Suite 4: Connection (TLS/STARTTLS)
# =============================================================================
def test_smtp_client_connect_use_tls_creates_smtp_and_starttls():
    """
    Test that _connect() with use_tls=True creates SMTP and calls starttls().

    Verifies STARTTLS path works for port 587.
    """
    # Arrange
    client = SMTPClient(host="smtp.test.com", port=587, use_tls=True)
    mock_server = MagicMock()

    # Act
    with patch('basefunctions.messaging.smtp_client.smtplib.SMTP', return_value=mock_server) as mock_smtp:
        client._connect()

    # Assert
    mock_smtp.assert_called_once_with("smtp.test.com", 587, timeout=30)
    mock_server.starttls.assert_called_once()


def test_smtp_client_connect_timeout_raises_smtp_error():
    """
    Test that _connect() raises SMTPError on connection timeout.

    Verifies error handling for connection timeouts.
    """
    # Arrange
    client = SMTPClient(host="smtp.test.com", port=587)

    # Act & Assert
    with patch('basefunctions.messaging.smtp_client.smtplib.SMTP', side_effect=TimeoutError("Connection timeout")):
        with pytest.raises(SMTPError, match="Connection timeout"):
            client._connect()


# =============================================================================
# Test Suite 5: Connection (SSL)
# =============================================================================
def test_smtp_client_connect_use_ssl_creates_smtp_ssl():
    """
    Test that _connect() with use_ssl=True creates SMTP_SSL and does NOT call starttls().

    Verifies SSL/implicit TLS path works for port 465.
    """
    # Arrange
    client = SMTPClient(host="smtp.test.com", port=465, use_ssl=True, use_tls=False)
    mock_server = MagicMock()

    # Act
    with patch('basefunctions.messaging.smtp_client.smtplib.SMTP_SSL', return_value=mock_server) as mock_smtp_ssl:
        client._connect()

    # Assert
    mock_smtp_ssl.assert_called_once_with("smtp.test.com", 465, timeout=30)
    mock_server.starttls.assert_not_called()


# =============================================================================
# Test Suite 6: Authentication (Login)
# =============================================================================
def test_smtp_client_login_calls_server_login():
    """
    Test that _login() calls server.login with correct credentials.

    Verifies login() method works correctly.
    """
    # Arrange
    client = SMTPClient(username="user@test.com", password="secret")
    mock_server = MagicMock()
    client._server = mock_server

    # Act
    client._login()

    # Assert
    mock_server.login.assert_called_once_with("user@test.com", "secret")


def test_smtp_client_login_auth_error_raises_smtp_error():
    """
    Test that _login() raises SMTPError on authentication failure.

    Verifies error handling for authentication failures.
    """
    # Arrange
    client = SMTPClient(username="user@test.com", password="wrong")
    mock_server = MagicMock()
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
    client._server = mock_server

    # Act & Assert
    with pytest.raises(SMTPError, match="Authentication failed"):
        client._login()


# =============================================================================
# Test Suite 7: Send Message
# =============================================================================
def test_smtp_client_send_calls_server_send_message():
    """
    Test that send() calls server.send_message with converted MIME message.

    Verifies email sending works correctly with message conversion.
    """
    # Arrange
    from unittest.mock import Mock

    client = SMTPClient(host="smtp.test.com", port=587)
    mock_server = Mock()
    client._server = mock_server

    msg = EmailMessage(to="user@test.com", subject="Test", body="Hello")

    # Act
    client.send(msg)

    # Assert
    mock_server.send_message.assert_called_once()
    call_args = mock_server.send_message.call_args[0][0]
    assert call_args['To'] == "user@test.com"


# =============================================================================
# Test Suite 8: Context Manager
# =============================================================================
def test_smtp_client_context_manager_connects_and_closes():
    """
    Test that context manager connects on entry and closes on exit.

    Verifies __enter__ calls _connect() and __exit__ calls close().
    """
    # Arrange
    mock_server = MagicMock()

    # Act
    with patch('basefunctions.messaging.smtp_client.smtplib.SMTP', return_value=mock_server):
        with SMTPClient(host="smtp.test.com", port=587, username="user@test.com", password="secret") as smtp:
            pass

    # Assert
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@test.com", "secret")
    mock_server.quit.assert_called_once()


def test_smtp_client_context_manager_calls_login_after_connect():
    """
    Test that context manager calls _login() after _connect().

    Verifies __enter__ establishes connection AND authenticates before returning.
    This is critical for send() to work - server must be authenticated.
    """
    # Arrange
    mock_server = MagicMock()
    call_order = []

    def track_starttls():
        call_order.append("starttls")

    def track_login(*args):
        call_order.append("login")

    mock_server.starttls = MagicMock(side_effect=track_starttls)
    mock_server.login = MagicMock(side_effect=track_login)

    # Act
    with patch('basefunctions.messaging.smtp_client.smtplib.SMTP', return_value=mock_server):
        with SMTPClient(host="smtp.test.com", port=587, username="user@test.com", password="secret") as smtp:
            pass

    # Assert
    # Verify both were called
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once()
    # Verify starttls came before login
    assert call_order == ["starttls", "login"]


# =============================================================================
# Test Suite 9: Convenience Function
# =============================================================================
def test_send_email_creates_message_and_sends():
    """
    Test that send_email() creates SMTPClient, creates message, and sends it.

    Verifies convenience function works with context manager and sends message.
    """
    # Arrange
    from basefunctions.messaging.smtp_client import send_email

    mock_client = MagicMock()
    mock_smtp_class = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_client
    mock_smtp_class.return_value.__exit__.return_value = None

    # Act
    with patch('basefunctions.messaging.smtp_client.SMTPClient', mock_smtp_class):
        send_email(to="user@test.com", subject="Test", body="Hello")

    # Assert
    mock_client.send.assert_called_once()
