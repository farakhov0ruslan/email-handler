import pytest

from notification_registry import NotificationChannel
from notification_registry import NotificationType
from notification_registry import deserialize_message
from notification_registry import serialize_message
from email_handler.consumer import build_on_max_retries
from email_handler.consumer import create_consumer
from email_handler.processor import process_email_message


class TestBuildOnMaxRetries:
    @pytest.fixture
    def publisher(self, mocker):
        return mocker.Mock()

    @pytest.fixture
    def published(self, publisher, reset_password_message):
        build_on_max_retries(publisher)(serialize_message(reset_password_message))
        raw = publisher.publish.call_args.kwargs["message"].encode()
        return deserialize_message(raw)

    def test_publishes_to_platform_queue(self, publisher, published):
        publisher.publish.assert_called_once()
        assert publisher.publish.call_args.kwargs["queue"] == NotificationChannel.PLATFORM.queue_name

    def test_message_is_delivery_failed_type(self, published):
        assert published.metadata.notification_type == NotificationType.DELIVERY_FAILED

    def test_preserves_recipient_email(self, published, reset_password_payload):
        assert published.payload.recipient_email == reset_password_payload.recipient_email

    def test_preserves_original_user_id(self, published, reset_password_payload):
        assert published.payload.user_id == reset_password_payload.user_id

    def test_original_channel_is_email(self, published):
        assert published.payload.original_channel == "email"

    def test_original_type_matches_source(self, published):
        assert published.payload.original_type == str(NotificationType.RESET_PASSWORD)

    def test_payload_without_phone_becomes_none(self, published):
        assert published.payload.recipient_phone is None

    def test_payload_without_webhook_url_becomes_none(self, published):
        assert published.payload.webhook_url is None

    def test_failed_at_is_tz_aware(self, published):
        assert published.payload.failed_at.tzinfo is not None

    def test_analytics_payload_also_handled(self, publisher, analytics_message):
        build_on_max_retries(publisher)(serialize_message(analytics_message))

        publisher.publish.assert_called_once()
        raw = publisher.publish.call_args.kwargs["message"].encode()
        assert deserialize_message(raw).metadata.notification_type == NotificationType.DELIVERY_FAILED


class TestCreateConsumer:
    @pytest.fixture
    def consumer_call_kwargs(self, mocker):
        consumer_cls = mocker.patch("email_handler.consumer.NotificationConsumer")
        create_consumer(mocker.Mock(name="rabbit_config"), mocker.Mock(name="publisher"))
        return consumer_cls.call_args.kwargs

    def test_queue_is_email(self, consumer_call_kwargs):
        assert consumer_call_kwargs["queue_name"] == NotificationChannel.EMAIL.queue_name

    def test_on_message_is_process_email_message(self, consumer_call_kwargs):
        assert consumer_call_kwargs["on_message"] is process_email_message

    def test_rabbitmq_config_forwarded(self, mocker):
        consumer_cls = mocker.patch("email_handler.consumer.NotificationConsumer")
        config = mocker.Mock(name="rabbit_config")

        create_consumer(config, mocker.Mock(name="publisher"))

        assert consumer_cls.call_args.kwargs["rabbitmq_config"] is config
