from notification_registry import ChannelHandlerSettings
from notification_registry import NotificationChannel
from notification_registry import NotificationConsumer
from notification_registry import create_channel_consumer
from utils_library.RabbitMQ.publisher import RabbitPublisher
from utils_library.RabbitMQ.rabbitmq import RabbitMQConfig

from email_handler.config import EMAIL_HANDLER_CONFIG
from email_handler.processor import process_email_message


def create_consumer(
    rabbitmq_config: RabbitMQConfig,
    publisher: RabbitPublisher,
) -> NotificationConsumer:
    settings = ChannelHandlerSettings(
        channel=NotificationChannel.EMAIL,
        max_retries=EMAIL_HANDLER_CONFIG.max_retries,
        retry_delay=EMAIL_HANDLER_CONFIG.retry_delay,
        failed_error_message="Email delivery failed after all retries",
    )
    return create_channel_consumer(
        settings=settings,
        on_message=process_email_message,
        publisher=publisher,
        rabbitmq_config=rabbitmq_config,
    )
