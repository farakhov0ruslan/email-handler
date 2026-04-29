from datetime import UTC
from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory

from notification_registry import AnalyticsPayload
from notification_registry import LinkedInDisconnectedPayload
from notification_registry import ResetPasswordPayload

EMAIL_ADDRESS = "user@example.com"


class ResetPasswordPayloadFactory(ModelFactory[ResetPasswordPayload]):
    reset_url = "https://example.com/reset?token=abc"
    expires_at = Use(lambda: datetime.now(UTC) + timedelta(hours=1))
    user_name = "Test User"
    user_ip = "127.0.0.1"
    user_agent = "test/1.0"
    recipient_phone = None
    webhook_url = None


class AnalyticsPayloadFactory(ModelFactory[AnalyticsPayload]):
    report_type = "weekly"
    period_start = Use(lambda: datetime.now(UTC) - timedelta(days=7))
    period_end = Use(lambda: datetime.now(UTC))
    total_leads = 100
    active_campaigns = 5
    engagement_rate = 42.5
    report_url = "https://example.com/reports/1"
    recipient_phone = None
    webhook_url = None


class LinkedInDisconnectedPayloadFactory(ModelFactory[LinkedInDisconnectedPayload]):
    reconnect_url = "https://example.com/linkedin/reconnect"
    disconnected_at = Use(lambda: datetime.now(UTC))
    reason = "session_expired"
    affected_campaigns = 3
    active_sequences = 2
    recipient_phone = None
    webhook_url = None
