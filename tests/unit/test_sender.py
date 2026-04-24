import asyncio
import base64
from unittest.mock import AsyncMock
from urllib.parse import parse_qs

import aiosmtplib
import httpx
import pytest
import respx

from email_handler.sender import EmailResult
from email_handler.sender import MailgunEmailSender
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
        mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config)

        result = asyncio.run(sender.send("to@example.com", "Subject", "<p>hi</p>"))

        assert result.status == "sent"
        assert result.to == "to@example.com"
        assert result.subject == "Subject"

    def test_calls_aiosmtplib_send_once(self, mocker, smtp_config):
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config)

        asyncio.run(sender.send("to@example.com", "Subject", "<p>hi</p>"))

        send_mock.assert_awaited_once()

    def test_returns_failed_on_smtp_exception(self, mocker, smtp_config):
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
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        kwargs = send_mock.call_args.kwargs
        assert "username" not in kwargs
        assert "password" not in kwargs

    def test_auth_kwargs_passed_when_credentials_set(self, mocker, smtp_config_with_auth):
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config_with_auth)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        kwargs = send_mock.call_args.kwargs
        assert kwargs["username"] == "user@x.com"
        assert kwargs["password"] == "secret"

    def test_from_email_used_over_username(self, mocker, smtp_config_with_from_email):
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config_with_from_email)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        message_arg = send_mock.call_args.args[0]
        assert message_arg["From"] == "from@example.com"

    def test_username_used_as_from_when_from_email_empty(self, mocker, smtp_config_with_auth):
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config_with_auth)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        message_arg = send_mock.call_args.args[0]
        assert message_arg["From"] == "user@x.com"

    def test_tls_flag_forwarded(self, mocker, smtp_config_tls_on):
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config_tls_on)

        asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        assert send_mock.call_args.kwargs["start_tls"] is True

    def test_text_body_creates_multipart(self, mocker, smtp_config):
        send_mock = mocker.patch("email_handler.sender.aiosmtplib.send", new_callable=AsyncMock)
        sender = SMTPEmailSender(smtp_config)

        asyncio.run(sender.send("to@example.com", "Subject", "<p>html</p>", text_body="plain"))

        message_arg = send_mock.call_args.args[0]
        assert message_arg.is_multipart()


class TestMailgunEmailSender:
    @pytest.fixture
    def endpoint(self, mailgun_config) -> str:
        return f"{mailgun_config.base_url}/v3/{mailgun_config.domain}/messages"

    def test_returns_sent_on_200(self, mailgun_config, endpoint):
        with respx.mock(assert_all_called=True) as mock:
            mock.post(endpoint).mock(
                return_value=httpx.Response(200, json={"id": "<msg@mg>", "message": "Queued"})
            )
            sender = MailgunEmailSender(mailgun_config)

            result = asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        assert result.status == "sent"
        assert result.message_id == "<msg@mg>"

    def test_returns_failed_on_4xx(self, mailgun_config, endpoint):
        with respx.mock() as mock:
            mock.post(endpoint).mock(
                return_value=httpx.Response(401, json={"message": "Unauthorized"})
            )
            sender = MailgunEmailSender(mailgun_config)

            result = asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        assert result.status == "failed"
        assert result.error_type == "HTTP401"
        assert "Unauthorized" in result.error

    def test_returns_failed_on_500(self, mailgun_config, endpoint):
        with respx.mock() as mock:
            mock.post(endpoint).mock(
                return_value=httpx.Response(500, json={"message": "Server Error"})
            )
            sender = MailgunEmailSender(mailgun_config)

            result = asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        assert result.status == "failed"
        assert result.error_type == "HTTP500"

    def test_returns_failed_on_connect_error(self, mailgun_config, endpoint):
        with respx.mock() as mock:
            mock.post(endpoint).mock(side_effect=httpx.ConnectError("refused"))
            sender = MailgunEmailSender(mailgun_config)

            result = asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        assert result.status == "failed"
        assert result.error_type == "ConnectError"

    def test_sends_basic_auth_header(self, mailgun_config, endpoint):
        with respx.mock() as mock:
            route = mock.post(endpoint).mock(
                return_value=httpx.Response(200, json={"id": "<x>", "message": "Queued"})
            )
            sender = MailgunEmailSender(mailgun_config)
            asyncio.run(sender.send("to@example.com", "Subject", "<p/>"))

        auth_header = route.calls.last.request.headers["authorization"]
        assert auth_header.startswith("Basic ")
        decoded = base64.b64decode(auth_header.split(" ")[1]).decode()
        assert decoded == f"api:{mailgun_config.api_key}"

    def test_text_body_included_in_form_data(self, mailgun_config, endpoint):
        with respx.mock() as mock:
            route = mock.post(endpoint).mock(
                return_value=httpx.Response(200, json={"id": "<x>", "message": "Queued"})
            )
            sender = MailgunEmailSender(mailgun_config)
            asyncio.run(sender.send("to@example.com", "Subject", "<p/>", text_body="plain text"))

        form = parse_qs(route.calls.last.request.content.decode())
        assert form["text"] == ["plain text"]


class TestGetEmailSender:
    @pytest.mark.parametrize("env_value", ["main", "production", "prod"])
    def test_returns_mailgun_for_prod_envs(self, monkeypatch, env_value):
        monkeypatch.setenv("env", env_value)

        sender = get_email_sender()

        assert isinstance(sender, MailgunEmailSender)

    @pytest.mark.parametrize("env_value", ["local", "dev", "test", ""])
    def test_returns_smtp_for_non_prod_envs(self, monkeypatch, env_value):
        monkeypatch.setenv("env", env_value)

        sender = get_email_sender()

        assert isinstance(sender, SMTPEmailSender)

    def test_returns_smtp_when_env_not_set(self, monkeypatch):
        monkeypatch.delenv("env", raising=False)

        sender = get_email_sender()

        assert isinstance(sender, SMTPEmailSender)

    def test_returns_same_instance_on_repeated_calls(self, monkeypatch):
        monkeypatch.setenv("env", "local")

        first = get_email_sender()
        second = get_email_sender()

        assert first is second
