import pytest

from notification_registry import NotificationType
import email_handler.sender as sender_module
from email_handler.config import MailgunConfiguration
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
    SMTPConfiguration.set_setting("smtp_host", "localhost")
    SMTPConfiguration.set_setting("smtp_port", 1025)
    SMTPConfiguration.set_setting("use_tls", False)
    SMTPConfiguration.set_setting("from_email", "dev@example.com")
    SMTPConfiguration.set_setting("username", "")
    SMTPConfiguration.set_setting("password", "")
    return SMTPConfiguration()


@pytest.fixture
def smtp_config_with_auth():
    SMTPConfiguration.set_setting("smtp_host", "localhost")
    SMTPConfiguration.set_setting("smtp_port", 1025)
    SMTPConfiguration.set_setting("use_tls", False)
    SMTPConfiguration.set_setting("from_email", "")
    SMTPConfiguration.set_setting("username", "user@x.com")
    SMTPConfiguration.set_setting("password", "secret")
    return SMTPConfiguration()


@pytest.fixture
def smtp_config_with_from_email():
    SMTPConfiguration.set_setting("smtp_host", "localhost")
    SMTPConfiguration.set_setting("smtp_port", 1025)
    SMTPConfiguration.set_setting("use_tls", False)
    SMTPConfiguration.set_setting("from_email", "from@example.com")
    SMTPConfiguration.set_setting("username", "user@x.com")
    SMTPConfiguration.set_setting("password", "")
    return SMTPConfiguration()


@pytest.fixture
def smtp_config_tls_on():
    SMTPConfiguration.set_setting("smtp_host", "localhost")
    SMTPConfiguration.set_setting("smtp_port", 1025)
    SMTPConfiguration.set_setting("use_tls", True)
    SMTPConfiguration.set_setting("from_email", "dev@example.com")
    SMTPConfiguration.set_setting("username", "")
    SMTPConfiguration.set_setting("password", "")
    return SMTPConfiguration()


@pytest.fixture
def mailgun_config():
    MailgunConfiguration.set_setting("api_key", "test-api-key")
    MailgunConfiguration.set_setting("domain", "mg.example.com")
    MailgunConfiguration.set_setting("base_url", "https://api.mailgun.net")
    MailgunConfiguration.set_setting("from_name", "TestApp")
    return MailgunConfiguration()


@pytest.fixture(autouse=True)
def _reset_sender_singleton():
    sender_module._email_sender = None
    yield
    sender_module._email_sender = None
