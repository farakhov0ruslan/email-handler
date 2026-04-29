import pytest

from notification_registry import NotificationChannel
from notification_registry import NotificationType
from notification_registry import deserialize_message
from notification_registry import serialize_message

from email_handler.consumer import create_consumer
from email_handler.processor import process_email_message


class TestCreateConsumer:
    @pytest.fixture
    def consumer_call_kwargs(self, mocker):
        consumer_cls = mocker.patch("notification_registry.channel_handler.NotificationConsumer")
        create_consumer(mocker.Mock(name="rabbit_config"), mocker.Mock(name="publisher"))
        return consumer_cls.call_args.kwargs

    def test_queue_is_email(self, consumer_call_kwargs):
        assert consumer_call_kwargs["queue_name"] == NotificationChannel.EMAIL.queue_name

    def test_on_message_is_process_email_message(self, consumer_call_kwargs):
        assert consumer_call_kwargs["on_message"] is process_email_message

    def test_rabbitmq_config_forwarded(self, mocker):
        consumer_cls = mocker.patch("notification_registry.channel_handler.NotificationConsumer")
        config = mocker.Mock(name="rabbit_config")

        create_consumer(config, mocker.Mock(name="publisher"))

        assert consumer_cls.call_args.kwargs["rabbitmq_config"] is config

    def test_max_retries_forwarded(self, mocker):
        consumer_cls = mocker.patch("notification_registry.channel_handler.NotificationConsumer")
        create_consumer(mocker.Mock(), mocker.Mock())
        from email_handler.config import EMAIL_HANDLER_CONFIG
        assert consumer_cls.call_args.kwargs["max_retries"] == EMAIL_HANDLER_CONFIG.max_retries

    def test_on_max_retries_publishes_delivery_failed(self, mocker, reset_password_message):
        publisher = mocker.Mock()
        consumer_cls = mocker.patch("notification_registry.channel_handler.NotificationConsumer")
        create_consumer(mocker.Mock(), publisher)

        on_max_retries = consumer_cls.call_args.kwargs["on_max_retries"]
        on_max_retries(serialize_message(reset_password_message))

        publisher.publish.assert_called_once()
        raw = publisher.publish.call_args.kwargs["message"].encode()
        msg = deserialize_message(raw)
        assert msg.metadata.notification_type == NotificationType.DELIVERY_FAILED
        assert publisher.publish.call_args.kwargs["queue"] == NotificationChannel.PLATFORM.queue_name
