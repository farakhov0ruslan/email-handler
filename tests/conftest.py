import pytest

from notification_registry import NotificationType
import email_handler.sender as sender_module
from email_handler.config import SMTPConfiguration
from tests.utils.factories import AnalyticsPayloadFactory
from tests.utils.factories import LinkedInDisconnectedPayloadFactory
from tests.utils.factories import ResetPasswordPayloadFactory
from tests.utils.messages import build_message


@pytest.fixture
def reset_password_payload():
    return ResetPasswordPayloadFactory.build()


@pytest.fixture
def analytics_payload():
    return AnalyticsPayloadFactory.build()


@pytest.fixture
def linkedin_disconnected_payload():
    return LinkedInDisconnectedPayloadFactory.build()


@pytest.fixture
def reset_password_message(reset_password_payload):
    return build_message(reset_password_payload, NotificationType.RESET_PASSWORD)


@pytest.fixture
def analytics_message(analytics_payload):
    return build_message(analytics_payload, NotificationType.ANALYTICS)


@pytest.fixture
def linkedin_disconnected_message(linkedin_disconnected_payload):
    return build_message(linkedin_disconnected_payload, NotificationType.LINKEDIN_DISCONNECTED)


@pytest.fixture
def smtp_config():
    return SMTPConfiguration(
        smtp_host="localhost",
        smtp_port=1025,
        use_tls=False,
        from_email="dev@example.com",
        username="",
        password="",
    )


@pytest.fixture
def smtp_config_with_auth():
    return SMTPConfiguration(
        smtp_host="localhost",
        smtp_port=1025,
        use_tls=False,
        from_email="",
        username="user@x.com",
        password="secret",
    )


@pytest.fixture
def smtp_config_with_from_email():
    return SMTPConfiguration(
        smtp_host="localhost",
        smtp_port=1025,
        use_tls=False,
        from_email="from@example.com",
        username="user@x.com",
        password="",
    )


@pytest.fixture
def smtp_config_tls_on():
    return SMTPConfiguration(
        smtp_host="localhost",
        smtp_port=1025,
        use_tls=True,
        from_email="dev@example.com",
        username="",
        password="",
    )


@pytest.fixture(autouse=True)
def _reset_sender_singleton():
    sender_module._sender = None
    yield
    sender_module._sender = None
