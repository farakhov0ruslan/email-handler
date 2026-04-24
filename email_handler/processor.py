import asyncio

from notification_registry import EmailChannelProcessor
from notification_registry import deserialize_message
from utils_library.Logging.log import get_logger

from email_handler.sender import get_email_sender

LOGGER = get_logger(__name__)


def process_email_message(body: bytes) -> None:
    message = deserialize_message(body)
    LOGGER.info(
        f"Processing email notification: type={message.metadata.notification_type}, "
        f"id={message.metadata.notification_id}"
    )

    processed = EmailChannelProcessor.process(message)
    if processed is None:
        raise RuntimeError(
            f"No email processor for type={message.metadata.notification_type}"
        )

    try:
        result = asyncio.run(
            get_email_sender().send(
                to_email=processed.recipient,
                subject=processed.subject or "",
                html_body=processed.body,
            )
        )
    except Exception as exc:
        LOGGER.exception(f"Unexpected error sending email to {processed.recipient}: {exc}")
        raise

    if result.status == "failed":
        LOGGER.error(
            f"Email delivery failed to {processed.recipient}: "
            f"[{result.error_type}] {result.error}"
        )
        raise RuntimeError(f"Email delivery failed to {processed.recipient}: {result.error}")

    LOGGER.info(
        f"Email sent: to={processed.recipient}, id={message.metadata.notification_id}"
    )
