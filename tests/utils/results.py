from email_handler.sender import EmailResult


def make_sent_result(to: str = "to@example.com", subject: str = "Subject") -> EmailResult:
    return EmailResult(status="sent", to=to, subject=subject, message_id="<msg-id@x>")


def make_failed_result(
    to: str = "to@example.com",
    subject: str = "Subject",
    error: str = "connection refused",
    error_type: str = "SMTPConnectError",
) -> EmailResult:
    return EmailResult(status="failed", to=to, subject=subject, error=error, error_type=error_type)
