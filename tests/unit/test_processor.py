import pytest

from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import serialize_message

from email_handler.processor import process_email_message
from tests.utils.messages import build_message
from tests.utils.mocks import mock_sender
from tests.utils.mocks import mock_sender_raising
from tests.utils.results import make_failed_result
from tests.utils.results import make_sent_result


class TestProcessEmailMessage:
    def test_reset_password_happy_path(self, mocker, reset_password_payload, reset_password_message):
        sender = mock_sender(mocker, make_sent_result(to=reset_password_payload.recipient_email))

        process_email_message(serialize_message(reset_password_message))

        sender.send.assert_awaited_once()
        call = sender.send.call_args
        assert call.kwargs["to_email"] == reset_password_payload.recipient_email
        assert call.kwargs["subject"] == "Password Reset Request"
        assert "<html" in call.kwargs["html_body"].lower()

    def test_analytics_happy_path(self, mocker, analytics_payload, analytics_message):
        sender = mock_sender(mocker, make_sent_result(to=analytics_payload.recipient_email))

        process_email_message(serialize_message(analytics_message))

        call = sender.send.call_args
        assert call.kwargs["to_email"] == analytics_payload.recipient_email
        assert analytics_payload.report_type in call.kwargs["subject"]

    def test_linkedin_disconnected_happy_path(
        self, mocker, linkedin_disconnected_payload, linkedin_disconnected_message
    ):
        sender = mock_sender(
            mocker, make_sent_result(to=linkedin_disconnected_payload.recipient_email)
        )

        process_email_message(serialize_message(linkedin_disconnected_message))

        call = sender.send.call_args
        assert call.kwargs["to_email"] == linkedin_disconnected_payload.recipient_email
        assert call.kwargs["subject"] == "LinkedIn Account Disconnected"

    def test_raises_runtime_error_when_sender_fails(self, mocker, reset_password_message):
        mock_sender(mocker, make_failed_result(error="SMTP timeout", error_type="SMTPException"))

        with pytest.raises(RuntimeError, match="SMTP timeout"):
            process_email_message(serialize_message(reset_password_message))

    def test_raises_when_sender_throws_exception(self, mocker, reset_password_message):
        mock_sender_raising(mocker, OSError("no route to host"))

        with pytest.raises(OSError, match="no route to host"):
            process_email_message(serialize_message(reset_password_message))

    def test_raises_when_processor_returns_none(self, mocker, reset_password_message):
        mocker.patch("email_handler.processor.EmailChannelProcessor.process", return_value=None)

        with pytest.raises(RuntimeError, match="No email processor"):
            process_email_message(serialize_message(reset_password_message))

    def test_raises_value_error_on_invalid_body(self):
        with pytest.raises(ValueError):
            process_email_message(b"not json at all")

    def test_html_body_not_empty(self, mocker, reset_password_message):
        sender = mock_sender(mocker, make_sent_result())

        process_email_message(serialize_message(reset_password_message))

        assert len(sender.send.call_args.kwargs["html_body"]) > 50

    def test_error_type_logged_on_failed_result(self, mocker, reset_password_message):
        mock_sender(mocker, make_failed_result(error_type="HTTP401", error="Unauthorized"))
        logger_mock = mocker.patch("email_handler.processor.LOGGER")

        with pytest.raises(RuntimeError):
            process_email_message(serialize_message(reset_password_message))

        error_calls = [str(c) for c in logger_mock.error.call_args_list]
        assert any("HTTP401" in c for c in error_calls)

    @pytest.mark.parametrize("priority", [NotificationPriority.LOW, NotificationPriority.HIGH])
    def test_processes_any_priority(self, mocker, reset_password_payload, priority):
        message = build_message(
            reset_password_payload,
            NotificationType.RESET_PASSWORD,
            priority=priority,
        )
        sender = mock_sender(mocker, make_sent_result())

        process_email_message(serialize_message(message))

        sender.send.assert_awaited_once()
