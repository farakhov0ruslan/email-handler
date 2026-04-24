from unittest.mock import AsyncMock

from pytest_mock import MockerFixture

from email_handler.sender import EmailResult


def mock_sender(mocker: MockerFixture, result: EmailResult):
    """Patch email_handler.processor.get_email_sender → Mock(send=AsyncMock(result))."""
    sender = mocker.Mock(send=AsyncMock(return_value=result))
    mocker.patch("email_handler.processor.get_email_sender", return_value=sender)
    return sender


def mock_sender_raising(mocker: MockerFixture, exc: BaseException):
    sender = mocker.Mock(send=AsyncMock(side_effect=exc))
    mocker.patch("email_handler.processor.get_email_sender", return_value=sender)
    return sender


def patched_publisher(mocker: MockerFixture):
    """Patch email_handler.client.RabbitPublisher to a MagicMock usable as context manager."""
    publisher = mocker.MagicMock()
    publisher.__enter__ = mocker.Mock(return_value=publisher)
    publisher.__exit__ = mocker.Mock(return_value=False)
    mocker.patch("email_handler.client.RabbitPublisher", return_value=publisher)
    return publisher
