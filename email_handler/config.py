from dataclasses import dataclass
from dataclasses import field

from utils_library.Configuration.meta_config import AbstractMetaConfig


@dataclass
class SMTPConfiguration(AbstractMetaConfig):
    smtp_host: str = field(
        default="smtp.gmail.com",
        metadata={"docs": "SMTP server hostname", "required": False},
    )
    smtp_port: int = field(
        default=587,
        metadata={"docs": "SMTP server port", "required": False},
    )
    username: str = field(
        default="",
        metadata={"docs": "SMTP username", "required": True},
    )
    password: str = field(
        default="",
        metadata={"docs": "SMTP password", "required": True, "hidden": True},
    )
    from_email: str = field(
        default="",
        metadata={"docs": "From email address (defaults to username)", "required": False},
    )
    use_tls: bool = field(
        default=True,
        metadata={"docs": "Use TLS for SMTP connection", "required": False},
    )


@dataclass
class MailgunConfiguration(AbstractMetaConfig):
    api_key: str = field(
        default="",
        metadata={"docs": "Mailgun API key", "required": True, "hidden": True},
    )
    domain: str = field(
        default="",
        metadata={"docs": "Mailgun domain (e.g. mg.salestrigger.io)", "required": True},
    )
    base_url: str = field(
        default="https://api.mailgun.net",
        metadata={
            "docs": "Mailgun API base URL (EU region uses https://api.eu.mailgun.net)",
            "required": False,
        },
    )
    from_name: str = field(
        default="SalesTrigger",
        metadata={"docs": "Display name for From header", "required": False},
    )


@dataclass
class EmailHandlerConfig(AbstractMetaConfig):
    environment: str = field(
        default="local",
        metadata={
            "docs": "Deployment environment (main/prod → Mailgun, иначе → SMTP)",
            "required": False,
        },
    )
    metrics_port: int = field(
        default=9093,
        metadata={"docs": "Prometheus metrics port", "required": False},
    )
    max_retries: int = field(
        default=5,
        metadata={"docs": "Max retry attempts for failed emails", "required": False},
    )
    retry_delay: float = field(
        default=2.0,
        metadata={"docs": "Delay between retries in seconds", "required": False},
    )


SMTP_CONFIG = SMTPConfiguration()
MAILGUN_CONFIG = MailgunConfiguration()
EMAIL_HANDLER_CONFIG = EmailHandlerConfig()
