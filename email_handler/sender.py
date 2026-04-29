from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from email.message import EmailMessage
from typing import Literal
from typing import Optional

import aiosmtplib
from utils_library.Logging.log import get_logger

from email_handler.config import SMTP_CONFIG
from email_handler.config import SMTPConfiguration

LOGGER = get_logger(__name__)


@dataclass
class EmailResult:
    status: Literal["sent", "failed"]
    to: str
    subject: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


class SMTPEmailSender:
    def __init__(self, config: SMTPConfiguration) -> None:
        self.config = config

    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> EmailResult:
        from_email = self.config.from_email or self.config.username

        message = EmailMessage()
        message["From"] = from_email
        message["To"] = to_email
        message["Subject"] = subject
        message["Date"] = datetime.now(UTC).strftime("%a, %d %b %Y %H:%M:%S +0000")

        if text_body:
            message.set_content(text_body)
            message.add_alternative(html_body, subtype="html")
        else:
            message.set_content(html_body, subtype="html")

        send_kwargs: dict = {
            "hostname": self.config.smtp_host,
            "port": self.config.smtp_port,
            "start_tls": self.config.use_tls,
            "timeout": 30,
        }
        if self.config.username and self.config.password:
            send_kwargs["username"] = self.config.username
            send_kwargs["password"] = self.config.password

        try:
            await aiosmtplib.send(message, **send_kwargs)
            LOGGER.info(f"SMTP sent: to={to_email}, subject={subject!r}")
            return EmailResult(
                status="sent",
                to=to_email,
                subject=subject,
                message_id=message.get("Message-ID"),
            )
        except aiosmtplib.SMTPException as e:
            LOGGER.error(f"SMTP error sending to {to_email}: {e}")
            return EmailResult(
                status="failed",
                to=to_email,
                subject=subject,
                error=str(e),
                error_type=type(e).__name__,
            )


_sender: Optional[SMTPEmailSender] = None


def get_email_sender() -> SMTPEmailSender:
    global _sender
    if _sender is None:
        _sender = SMTPEmailSender(SMTP_CONFIG)
    return _sender
