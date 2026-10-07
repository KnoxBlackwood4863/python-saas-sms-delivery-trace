from src.tenant_sms import TenantOnboarding, onboard_admin


class FakeClient:
    def __init__(self):
        self.calls = []

    def send_sms(self, phone, text, request_id):
        self.calls.append(("send", phone, request_id))
        return {"ok": True, "data": {"message_id": "m-42"}}

    def sms_events(self, message_id):
        self.calls.append(("events", message_id))
        return {"ok": True, "data": {"status": "delivered", "message_id": message_id}}

    def report_metric(self, name, value, tenant_id):
        self.calls.append(("metric", name, value, tenant_id))
        return {"ok": True, "data": {}}


def test_onboarding_answers_delivery_without_a_dashboard_join():
    client = FakeClient()
    answer = onboard_admin(TenantOnboarding("t-7", "+15550001", "Lee"), client)
    assert answer.delivered is True
    assert answer.message_id == "m-42"
    assert client.calls == [
        ("send", "+15550001", "onboarding:t-7"),
        ("events", "m-42"),
        ("metric", "tenant_onboarding_sms_delivered", 1.0, "t-7"),
    ]
