"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment, Munich
 Project : basefunctions
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Tests for EmailMessage class
 Log:
 v1.0.0 : Initial implementation
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================
from email.message import EmailMessage as StdEmailMessage

import pytest

from basefunctions.messaging.email_message import EmailMessage, EmailError


# =============================================================================
# TEST CASES
# =============================================================================
def test_email_message_init_valid_creates_message():
    """
    Test that EmailMessage initializes correctly with valid parameters.

    Arrange: Valid email parameters
    Act: Create EmailMessage instance
    Assert: Instance attributes are set correctly
    """
    # Arrange
    to = "test@example.com"
    subject = "Test Subject"
    body = "Test Body"
    from_addr = "sender@example.com"

    # Act
    msg = EmailMessage(to=to, subject=subject, body=body, from_addr=from_addr)

    # Assert
    assert msg.to == to
    assert msg.subject == subject
    assert msg.body == body
    assert msg.from_addr == from_addr


def test_validate_email_valid_format_returns_true():
    """
    Test that _validate_email returns True for valid email formats.

    Arrange: Valid email address
    Act: Call _validate_email
    Assert: Returns True
    """
    # Arrange
    valid_email = "test@example.com"

    # Act
    result = EmailMessage._validate_email(valid_email)

    # Assert
    assert result is True


def test_validate_email_invalid_format_raises_error():
    """
    Test that _validate_email raises EmailError for invalid email formats.

    Arrange: Invalid email address
    Act: Call _validate_email
    Assert: Raises EmailError with correct message
    """
    # Arrange
    invalid_email = "invalid-email"

    # Act & Assert
    with pytest.raises(EmailError) as exc_info:
        EmailMessage._validate_email(invalid_email)

    assert "Invalid email format" in str(exc_info.value)


def test_email_message_init_missing_to_raises_error():
    """
    Test that EmailMessage raises EmailError when required fields are missing.

    Arrange: Missing or empty required field (to)
    Act: Try to create EmailMessage
    Assert: Raises EmailError with correct message
    """
    # Arrange
    subject = "Test Subject"
    body = "Test Body"

    # Act & Assert - missing 'to'
    with pytest.raises(EmailError) as exc_info:
        EmailMessage(to="", subject=subject, body=body)

    assert "'to' is required" in str(exc_info.value)

    # Act & Assert - None 'to'
    with pytest.raises(EmailError) as exc_info:
        EmailMessage(to=None, subject=subject, body=body)

    assert "'to' is required" in str(exc_info.value)

    # Act & Assert - empty subject
    with pytest.raises(EmailError) as exc_info:
        EmailMessage(to="test@example.com", subject="", body=body)

    assert "'subject' is required" in str(exc_info.value)

    # Act & Assert - empty body
    with pytest.raises(EmailError) as exc_info:
        EmailMessage(to="test@example.com", subject=subject, body="")

    assert "'body' is required" in str(exc_info.value)


def test_to_mime_message_returns_std_email_message():
    """
    Test that to_mime_message returns a properly formatted standard email message.

    Arrange: Valid EmailMessage instance
    Act: Call to_mime_message
    Assert: Returns StdEmailMessage with correct headers and content
    """
    # Arrange
    to = "recipient@example.com"
    subject = "Test Subject"
    body = "Test Body Content"
    from_addr = "sender@example.com"
    msg = EmailMessage(to=to, subject=subject, body=body, from_addr=from_addr)

    # Act
    mime_msg = msg.to_mime_message()

    # Assert
    assert isinstance(mime_msg, StdEmailMessage)
    assert mime_msg["To"] == to
    assert mime_msg["Subject"] == subject
    assert mime_msg["From"] == from_addr
    assert mime_msg.get_content().strip() == body

    # Test with default from_addr
    msg_no_from = EmailMessage(to=to, subject=subject, body=body)
    mime_msg_no_from = msg_no_from.to_mime_message()
    assert mime_msg_no_from["From"] == "noreply@example.com"
