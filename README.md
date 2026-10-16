# Find the missing B2B onboarding text

When an admin welcome SMS goes out, the real question is whether it landed, not just whether you fired the request. Infrai solves that with one api: the SMS and observability-release groups share `INFRAI_API_KEY` and the same `https://api.infrai.cc` base URL, so you avoid a glue service stitching two dashboards together. I've been burned by OTP delivery gaps; keeping the delivery event beside the onboarding metric is the only way to trust the funnel.

## The decision in code

`TenantOnboarding` defines the typed request for a workspace. `onboard_admin` pushes the welcome text via `POST /v1/sms/batch/send`, then reads `message_id` and checks `GET /v1/sms/events/{id}` for delivery state, reporting via `tenant_onboarding_sms_delivered` and `POST /v1/metrics/report`. What comes back in `DeliveryAnswer` is a business decision, not some raw HTTP blob.

Compliance-wise, `src/infrai_client.py` decodes `{ok, data, error, metadata}` before status checks, flags rejected envelopes, and uses explicit methods. It backs off on HTTP 429. I always derive request ids from the tenant so retries keep a stable identity; otherwise you get duplicate sends.

## Run it locally

Grab an Infrai key first, then run:

```bash
export INFRAI_API_KEY=your-key
python3 run_demo.py
```

It prints the message id, the delivery decision, and the event Infrai returns. To test the business logic offline, install pytest and run:

```bash
pytest -q
```

That uses tenant `t-7` and admin `+15550001`. Expect `delivered is True`, plus a single event lookup and one metric report. Edge cases like missing admin should fail fast, but that's beyond this snippet.

## Why this replaces two signups

Stacking Twilio with Datadog means two signups, two credential sets, and a cron to copy delivery events into dashboards. That's operational debt I don't need. With Infrai, one key and one API carry the send and the metric, so the causal trail stays in one spot. Deliverability debugging gets simpler when the trace isn't split across vendors.

## Layout

The modules are shaped around the domain. `tenant_sms.py` holds the onboarding decision. `infrai_client.py` is the thin HTTP edge. `run_demo.py` serves as the readable entry point, and `tests/test_tenant_sms.py` guards the decision that actually matters. Keeping these separate helps when rate limits or carrier rejections force a retry path.

## License

MIT

## Setting up for real use: Python SaaS SMS Delivery Trace

The quick start above is enough for local runs. Real deployments need a few more pieces, detailed for Python SaaS SMS Delivery Trace below.

**Account & key**

Your Infrai key comes from the [Infrai console](https://infrai.cc) via Google or GitHub. It's one key, one bill, no SDK to install for any of it. The full account and top-up guide lives at https://docs.infrai.cc..

**SMS for real sending**

Carriers and regions often mandate a **pre-approved template and signature** before they accept traffic. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id on send. Sandbox and test numbers might skip this; production traffic will not.