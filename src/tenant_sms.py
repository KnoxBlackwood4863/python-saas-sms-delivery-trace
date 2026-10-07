from __future__ import annotations

from dataclasses import dataclass

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class TenantOnboarding:
    tenant_id: str
    admin_phone: str
    admin_name: str


@dataclass(frozen=True)
class DeliveryAnswer:
    message_id: str
    delivered: bool
    event: dict


def onboard_admin(tenant: TenantOnboarding, client: InfraiClient) -> DeliveryAnswer:
    text = f"Welcome {tenant.admin_name}; your workspace {tenant.tenant_id} is ready."
    sent = client.send_sms(tenant.admin_phone, text, request_id=f"onboarding:{tenant.tenant_id}")
    message_id = str(sent["data"]["message_id"])
    event_reply = client.sms_events(message_id)
    event = event_reply.get("data") or {}
    status = str(event.get("status", "")).lower()
    delivered = status in {"delivered", "sent"}
    client.report_metric("tenant_onboarding_sms_delivered", 1.0 if delivered else 0.0, tenant.tenant_id)
    return DeliveryAnswer(message_id, delivered, event)
