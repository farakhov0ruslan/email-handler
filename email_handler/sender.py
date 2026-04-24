import os
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from email.message import EmailMessage
from typing import Literal
from typing import Optional

import aiosmtplib
import httpx
from utils_library.Logging.log import get_logger

from email_handler.config import MAILGUN_CONFIG
from email_handler.config import SMTP_CONFIG
from email_handler.config import MailgunConfiguration
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


class EmailSender(ABC):
    @abstractmethod
    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> EmailResult:
        ...


class SMTPEmailSender(EmailSender):
    """Отправка через SMTP (aiosmtplib). Используется локально/в dev."""

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
            LOGGER.info(f"SMTP sent to {to_email}, subject={subject}")
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


class MailgunEmailSender(EmailSender):
    """Отправка через Mailgun HTTP API.

    POST {base_url}/v3/{domain}/messages
    Basic auth: api:<api_key>, multipart/form-data.
    Docs: https://documentation.mailgun.com/docs/mailgun/api-reference/send/mailgun/messages
    """

    def __init__(self, config: MailgunConfiguration) -> None:
        self.config = config
        self._endpoint = f"{config.base_url}/v3/{config.domain}/messages"
        self._from = f"{config.from_name} <mailgun@{config.domain}>"

    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> EmailResult:
        data = {
            "from": self._from,
            "to": to_email,
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            data["text"] = text_body

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    self._endpoint,
                    data=data,
                    auth=("api", self.config.api_key),
                )
                body = resp.json()
                if resp.status_code == 200:
                    LOGGER.info(
                        f"Mailgun sent to {to_email}, "
                        f"subject={subject}, id={body.get('id')}"
                    )
                    return EmailResult(
                        status="sent",
                        to=to_email,
                        subject=subject,
                        message_id=body.get("id"),
                    )
                LOGGER.error(
                    f"Mailgun error status={resp.status_code} body={body} to={to_email}"
                )
                return EmailResult(
                    status="failed",
                    to=to_email,
                    subject=subject,
                    error=str(body.get("message") or body),
                    error_type=f"HTTP{resp.status_code}",
                )
        except httpx.HTTPError as e:
            LOGGER.error(f"Mailgun HTTP error sending to {to_email}: {e}")
            return EmailResult(
                status="failed",
                to=to_email,
                subject=subject,
                error=str(e),
                error_type=type(e).__name__,
            )


_email_sender: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    global _email_sender
    if _email_sender is None:
        match os.getenv("env"):
            case "main" | "production" | "prod":
                _email_sender = MailgunEmailSender(MAILGUN_CONFIG)
            case _:
                _email_sender = SMTPEmailSender(SMTP_CONFIG)
    return _email_sender
