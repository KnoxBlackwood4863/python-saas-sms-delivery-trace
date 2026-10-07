from src.infrai_client import InfraiClient
from src.tenant_sms import TenantOnboarding, onboard_admin


if __name__ == "__main__":
    tenant = TenantOnboarding("acme-eu", "+15551234567", "Ari")
    answer = onboard_admin(tenant, InfraiClient())
    print({"message_id": answer.message_id, "delivered": answer.delivered, "event": answer.event})
