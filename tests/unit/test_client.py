import pytest

from notification_registry import NotificationChannel
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import deserialize_message
from notification_registry.models import ResetPasswordPayload
from email_handler.client import send_email
from tests.utils.mocks import patched_publisher


class TestSendEmail:
    @pytest.fixture
    def publisher(self, mocker):
        return patched_publisher(mocker)

    @staticmethod
    def _published_message(publisher):
        raw = publisher.publish.call_args.kwargs["message"].encode()
        return deserialize_message(raw)

    def test_publishes_to_email_queue(self, publisher, reset_password_payload):
        send_email(reset_password_payload)

        publisher.publish.assert_called_once()
        assert publisher.publish.call_args.kwargs["queue"] == NotificationChannel.EMAIL.queue_name

    @pytest.mark.parametrize(
        "payload_fixture, expected_type",
        [
            ("reset_password_payload", NotificationType.RESET_PASSWORD),
            ("analytics_payload", NotificationType.ANALYTICS),
            ("linkedin_disconnected_payload", NotificationType.LINKEDIN_DISCONNECTED),
        ],
    )
    def test_notification_type_matches_payload(
        self, publisher, request, payload_fixture, expected_type
    ):
        payload = request.getfixturevalue(payload_fixture)

        send_email(payload)

        assert self._published_message(publisher).metadata.notification_type == expected_type

    def test_priority_forwarded_to_metadata(self, publisher, reset_password_payload):
        send_email(reset_password_payload, priority=NotificationPriority.HIGH)

        assert self._published_message(publisher).metadata.priority == NotificationPriority.HIGH

    def test_default_priority_is_normal(self, publisher, reset_password_payload):
        send_email(reset_password_payload)

        assert self._published_message(publisher).metadata.priority == NotificationPriority.NORMAL

    def test_channel_is_always_email(self, publisher, analytics_payload):
        send_email(analytics_payload)

        assert self._published_message(publisher).metadata.channel == NotificationChannel.EMAIL

    def test_declare_queue_true(self, publisher, reset_password_payload):
        send_email(reset_password_payload)

        assert publisher.publish.call_args.kwargs["declare_queue"] is True

    def test_unknown_payload_raises_value_error(self, publisher):
        class UnknownPayload:
            pass

        with pytest.raises(ValueError, match="Unknown payload type"):
            send_email(UnknownPayload())  # type: ignore[arg-type]

    def test_publisher_context_manager_exits(self, publisher, reset_password_payload):
        send_email(reset_password_payload)

        publisher.__exit__.assert_called_once()

    def test_payload_preserved_in_message(self, publisher, reset_password_payload):
        send_email(reset_password_payload)

        msg = self._published_message(publisher)
        assert isinstance(msg.payload, ResetPasswordPayload)
        assert msg.payload.user_id == reset_password_payload.user_id
