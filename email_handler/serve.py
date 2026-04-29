import signal

import fire
from notification_registry import NotificationChannel
from prometheus_client import start_http_server
from utils_library.Logging.log import configure_logger
from utils_library.Logging.log import get_logger
from utils_library.RabbitMQ.correct_consumer import ThreadedRabbitConsumer
from utils_library.RabbitMQ.publisher import RabbitPublisher
from utils_library.RabbitMQ.rabbitmq import RABBIT_MQ_CONFIG

from email_handler.config import EMAIL_HANDLER_CONFIG
from email_handler.consumer import create_consumer

LOGGER = get_logger(__name__)


def serve() -> None:
    LOGGER.info("Starting email-handler")
    start_http_server(EMAIL_HANDLER_CONFIG.metrics_port)
    LOGGER.info(f"Prometheus metrics on :{EMAIL_HANDLER_CONFIG.metrics_port}")

    with RabbitPublisher(RABBIT_MQ_CONFIG) as publisher:
        consumer = create_consumer(RABBIT_MQ_CONFIG, publisher)
        threaded = ThreadedRabbitConsumer(consumer)

        def _shutdown(signum, _frame) -> None:
            LOGGER.info(f"Received signal {signum}, shutting down gracefully...")
            threaded.stop()

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        LOGGER.info(f"Email handler started, listening on {NotificationChannel.EMAIL.queue_name}")
        threaded.start()
        threaded.join()

    LOGGER.info("Email handler stopped")


if __name__ == "__main__":  # pragma: no cover
    configure_logger("email_handler", "INFO", json_logger=True)
    configure_logger(__name__, "INFO", json_logger=True)
    fire.Fire(serve)
