"""LocalNotificationClient → process_email_message → мокнутый sender. Без RabbitMQ и SMTP."""
import pytest

from notification_registry import LocalNotificationClient
from notification_registry import NotificationChannel

from email_handler.processor import process_email_message
from tests.utils.factories import EMAIL_ADDRESS
from tests.utils.messages import build_email_message
from tests.utils.mocks import mock_sender
from tests.utils.results import make_failed_result
from tests.utils.results import make_sent_result


def _run_pipeline(client: LocalNotificationClient, message) -> None:
    with client:
        client.publish(message)


def _in_process_handler(queue_name: str, body: bytes) -> None:
    process_email_message(body)


class TestLocalPipeline:
    @pytest.mark.parametrize(
        "payload_fixture",
        ["reset_password_payload", "analytics_payload", "linkedin_disconnected_payload"],
    )
    def test_payload_reaches_sender(self, mocker, request, payload_fixture):
        payload = request.getfixturevalue(payload_fixture)
        sender = mock_sender(mocker, make_sent_result(to=EMAIL_ADDRESS))
        message = build_email_message(payload)

        _run_pipeline(LocalNotificationClient(handler=_in_process_handler), message)

        sender.send.assert_awaited_once()
        assert sender.send.call_args.kwargs["to_email"] == EMAIL_ADDRESS

    def test_message_stored_in_published(self, mocker, reset_password_payload):
        mock_sender(mocker, make_sent_result())
        message = build_email_message(reset_password_payload)

        with LocalNotificationClient(handler=_in_process_handler) as client:
            client.publish(message)
            client.publish(message)

            assert len(client.published) == 2

    def test_published_queue_name_is_email(self, mocker, reset_password_payload):
        mock_sender(mocker, make_sent_result())
        message = build_email_message(reset_password_payload)

        with LocalNotificationClient(handler=_in_process_handler) as client:
            client.publish(message)

            queue_name, _ = client.published[0]

        assert queue_name == NotificationChannel.EMAIL.queue_name

    def test_sender_failure_propagates_from_handler(self, mocker, reset_password_payload):
        mock_sender(mocker, make_failed_result(error="SMTP down"))
        message = build_email_message(reset_password_payload)

        with pytest.raises(RuntimeError, match="SMTP down"):
            _run_pipeline(LocalNotificationClient(handler=_in_process_handler), message)
