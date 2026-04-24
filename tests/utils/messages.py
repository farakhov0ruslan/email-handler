from uuid import uuid4

from notification_registry import BaseNotificationPayload
from notification_registry import NotificationChannel
from notification_registry import NotificationMessage
from notification_registry import NotificationMetadata
from notification_registry import NotificationPriority
from notification_registry import NotificationType
from notification_registry.serialization import PAYLOAD_TYPE_MAPPING

_PAYLOAD_TO_TYPE: dict[type, NotificationType] = {
    payload_cls: notification_type
    for notification_type, payload_cls in PAYLOAD_TYPE_MAPPING.items()
}


def build_message(
    payload: BaseNotificationPayload,
    notification_type: NotificationType,
    channel: NotificationChannel = NotificationChannel.EMAIL,
    priority: NotificationPriority = NotificationPriority.NORMAL,
) -> NotificationMessage:
    return NotificationMessage(
        metadata=NotificationMetadata(
            notification_id=uuid4(),
            notification_type=notification_type,
            channel=channel,
            priority=priority,
        ),
        payload=payload,
    )


def build_email_message(
    payload: BaseNotificationPayload,
    priority: NotificationPriority = NotificationPriority.NORMAL,
) -> NotificationMessage:
    notification_type = _PAYLOAD_TO_TYPE[type(payload)]
    return build_message(payload, notification_type, NotificationChannel.EMAIL, priority)
