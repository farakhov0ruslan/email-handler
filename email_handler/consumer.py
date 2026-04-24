from datetime import UTC
from datetime import datetime
from typing import Callable

from notification_registry import NotificationChannel
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry import DeliveryFailedPayload
from notification_registry import deserialize_message
from notification_registry import serialize_message

from notification_service.utils import NotificationConsumer

from utils_library.Logging.log import get_logger
from utils_library.RabbitMQ.publisher import RabbitPublisher
from utils_library.RabbitMQ.rabbitmq import RabbitMQConfig

from email_handler.config import EMAIL_HANDLER_CONFIG
from email_handler.processor import process_email_message

LOGGER = get_logger(__name__)


def build_on_max_retries(publisher: RabbitPublisher) -> Callable[[bytes], None]:

    def on_max_retries(body: bytes) -> None:
        original = deserialize_message(body)
        LOGGER.error(
            f"Max retries exhausted for notification_id={original.metadata.notification_id}, "
            f"type={original.metadata.notification_type}. "
            f"Publishing DELIVERY_FAILED to notification.platform"
        )

        failed_msg = NotificationMessage(
            metadata=NotificationMetadata(
                notification_type=NotificationType.DELIVERY_FAILED,
                channel=NotificationChannel.PLATFORM,
                priority=NotificationPriority.HIGH,
            ),
            payload=DeliveryFailedPayload(
                user_id=original.payload.user_id,
                recipient_email=original.payload.recipient_email,
                recipient_phone=getattr(original.payload, "recipient_phone", None),
                webhook_url=getattr(original.payload, "webhook_url", None),
                original_channel="email",
                original_type=str(original.metadata.notification_type),
                error_message="Email delivery failed after all retries",
                retry_count=EMAIL_HANDLER_CONFIG.max_retries,
                failed_at=datetime.now(UTC),
            ),
        )

        publisher.publish(
            message=serialize_message(failed_msg).decode("utf-8"),
            queue=NotificationChannel.PLATFORM.queue_name,
        )

    return on_max_retries


def create_consumer(
    rabbitmq_config: RabbitMQConfig,
    publisher: RabbitPublisher,
) -> NotificationConsumer:
    """Create a NotificationConsumer for the notification.email queue."""
    return NotificationConsumer(
        queue_name=NotificationChannel.EMAIL.queue_name,
        on_message=process_email_message,
        on_max_retries=build_on_max_retries(publisher),
        rabbitmq_config=rabbitmq_config,
        max_retries=EMAIL_HANDLER_CONFIG.max_retries,
        retry_delay=EMAIL_HANDLER_CONFIG.retry_delay,
    )
