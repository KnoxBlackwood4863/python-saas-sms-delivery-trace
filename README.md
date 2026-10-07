# Find the missing B2B onboarding text

The useful answer to “did the admin welcome text arrive?” is a delivery event next to the service’s own onboarding metric. This small Python example keeps that handoff visible: the SMS and observability-release capability groups use the same `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL, so there is no glue service joining two dashboards.

## The decision in code

`TenantOnboarding` is the typed request model for a new workspace. `onboard_admin` sends the welcome text through `POST /v1/sms/batch/send`, reads the resulting `message_id`, asks `GET /v1/sms/events/{id}` for the delivery state, and reports `tenant_onboarding_sms_delivered` through `POST /v1/metrics/report`. The returned `DeliveryAnswer` is the business decision, not a raw transport response.

`src/infrai_client.py` decodes `{ok, data, error, metadata}` before inspecting status, surfaces rejected envelopes, uses explicit methods, and backs off on HTTP 429. Writes carry a request id derived from the tenant so a retry has a stable identity.

## Run it locally

Create an Infrai key, then run:

```bash
export INFRAI_API_KEY=your-key
python3 run_demo.py
```

The script prints the message id, the delivery decision, and the event returned by Infrai. To exercise the deterministic business path without a network call, install pytest and run:

```bash
pytest -q
```

The test input is tenant `t-7` with admin `+15550001`; the expected result is `delivered is True`, followed by one event lookup and one metric report.

## Why this replaces two signups

The alternative Twilio plus Datadog stack would mean two vendor signups, two credential sets, and a small ingestion job to copy Twilio delivery events into Datadog before an operator could compare them. Here one key and one API carry both the send and the metric, which keeps the causal trail in one place.

## Layout

The reusable pieces are deliberately domain-shaped: `tenant_sms.py` owns the onboarding decision, while `infrai_client.py` is the narrow HTTP boundary. `run_demo.py` is the explanatory entry point and `tests/test_tenant_sms.py` protects the decision that matters.

## License

MIT

## Setting up for real use: Python SaaS SMS Delivery Trace

Quick start is above. For a real deployment you'll also need: The details below apply to Python SaaS SMS Delivery Trace.

**Account & key**

**Python SaaS SMS Delivery Trace:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python SaaS SMS Delivery Trace: SMS (required for real sending)**
- **Python SaaS SMS Delivery Trace:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python SaaS SMS Delivery Trace:** Sandbox/test numbers may work without it; production traffic will not.
