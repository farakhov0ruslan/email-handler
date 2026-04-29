from dataclasses import dataclass
from dataclasses import field

from utils_library.Configuration.meta_config import AbstractMetaConfig


@dataclass
class SMTPConfiguration(AbstractMetaConfig):
    smtp_host: str = field(
        default="localhost",
        metadata={"docs": "SMTP server hostname", "required": True},
    )
    smtp_port: int = field(
        default=587,
        metadata={"docs": "SMTP server port", "required": False},
    )
    username: str = field(
        default="",
        metadata={"docs": "SMTP username (login)", "required": False},
    )
    password: str = field(
        default="",
        metadata={"docs": "SMTP password", "required": False, "hidden": True},
    )
    from_email: str = field(
        default="",
        metadata={"docs": "From address (defaults to username if empty)", "required": False},
    )
    use_tls: bool = field(
        default=True,
        metadata={"docs": "Use STARTTLS", "required": False},
    )


@dataclass
class EmailHandlerConfig(AbstractMetaConfig):
    metrics_port: int = field(
        default=9090,
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
EMAIL_HANDLER_CONFIG = EmailHandlerConfig()
