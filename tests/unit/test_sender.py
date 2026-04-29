import asyncio

import aiosmtplib
import pytest

from email_handler.sender import EmailResult
from email_handler.sender import SMTPEmailSender
from email_handler.sender import get_email_sender


class TestEmailResult:
    def test_timestamp_auto_populated(self):
        result = EmailResult(status="sent", to="x@x.com", subject="s")

        assert result.timestamp != ""
        assert "T" in result.timestamp

    def test_explicit_empty_timestamp_gets_auto_filled(self):
        result = EmailResult(status="sent", to="x@x.com", subject="s", timestamp="")

        assert result.timestamp != ""

    def test_explicit_timestamp_not_overwritten(self):
        result = EmailResult(status="sent", to="x@x.com", subject="s", timestamp="2026-01-01T00:00:00")

        assert result.timestamp == "2026-01-01T00:00:00"

    def test_optional_fields_default_none(self):
        result = EmailResult(status="sent", to="x@x.com", subject="s")

        assert result.message_id is None
        assert result.error is None
        assert result.error_type is None


class TestSMTPEmailSender:
    def test_returns_sent_on_success(self, mocker, smtp_config):
        mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=pytest.importorskip("unittest.mock").AsyncMock)
        sender = SMTPEmailSender(smtp_config)

        result = asyncio.run(sender.send("to@example.com", "Subject", "<p>hi</p>"))

        assert result.status == "sent"
        assert result.to == "to@example.com"
        assert result.subject == "Subject"

    def test_calls_aiosmtplib_send_once(self, mocker, smtp_config):
        from unittest.mock import AsyncMock
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config)

        asyncio.run(sender.send("to@example.com", "Subject", "<p>hi</p>"))

        send_mock.assert_awaited_once()

    def test_returns_failed_on_smtp_exception(self, mocker, smtp_config):
        from unittest.mock import AsyncMock
        mocker.patch(
            "email_handler.sender.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=aiosmtplib.SMTPException("boom"),
        )
        sender = SMTPEmailSender(smtp_config)

        result = asyncio.run(sender.send("to@example.com", "Subject", "<p>hi</p>"))

        assert result.status == "failed"
        assert result.error == "boom"
        assert result.error_type == "SMTPException"

    def test_no_auth_kwargs_when_credentials_empty(self, mocker, smtp_config):
        from unittest.mock import AsyncMock
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        kwargs = send_mock.call_args.kwargs
        assert "username" not in kwargs
        assert "password" not in kwargs

    def test_auth_kwargs_passed_when_credentials_set(self, mocker, smtp_config_with_auth):
        from unittest.mock import AsyncMock
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config_with_auth)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        kwargs = send_mock.call_args.kwargs
        assert kwargs["username"] == "user@x.com"
        assert kwargs["password"] == "secret"

    def test_from_email_used_over_username(self, mocker, smtp_config_with_from_email):
        from unittest.mock import AsyncMock
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config_with_from_email)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        message_arg = send_mock.call_args.args[0]
        assert message_arg["From"] == "from@example.com"

    def test_username_used_as_from_when_from_email_empty(self, mocker, smtp_config_with_auth):
        from unittest.mock import AsyncMock
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config_with_auth)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        message_arg = send_mock.call_args.args[0]
        assert message_arg["From"] == "user@x.com"

    def test_tls_flag_forwarded(self, mocker, smtp_config_tls_on):
        from unittest.mock import AsyncMock
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config_tls_on)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        assert send_mock.call_args.kwargs["start_tls"] is True

    def test_text_body_creates_multipart(self, mocker, smtp_config):
        from unittest.mock import AsyncMock
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config)

        asyncio.run(sender.send("to@example.com", "Subject", "<p>html</p>", text_body="plain"))

        message_arg = send_mock.call_args.args[0]
        assert message_arg.is_multipart()


class TestGetEmailSender:
    def test_returns_smtp_sender(self):
        sender = get_email_sender()

        assert isinstance(sender, SMTPEmailSender)

    def test_returns_same_instance_on_repeated_calls(self):
        first = get_email_sender()
        second = get_email_sender()

        assert first is second
