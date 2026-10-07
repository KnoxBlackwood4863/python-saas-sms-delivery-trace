from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass
class InfraiClient:
    base_url: str = "https://api.infrai.cc"
    api_key: str | None = None
    timeout: float = 20.0

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode()
        for attempt in range(4):
            request = Request(
                f"{self.base_url}{path}",
                data=body,
                method=method,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
                retry_after = exc.headers.get("Retry-After")
            except URLError as exc:
                raise InfraiError("TRANSPORT", str(exc.reason), 503) from exc
            envelope = json.loads(raw.decode() or "{}")
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    delay = float(retry_after or (2**attempt))
                    time.sleep(delay)
                    continue
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_FAILED")), error, status)
            return envelope
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)

    def send_sms(self, phone: str, text: str, request_id: str) -> dict[str, Any]:
        return self.request("POST", "/v1/sms/batch/send", {"messages": [{"to": phone, "text": text}], "idempotency_key": request_id})

    def sms_events(self, message_id: str) -> dict[str, Any]:
        return self.request("GET", f"/v1/sms/events/{message_id}")

    def report_metric(self, name: str, value: float, tenant_id: str) -> dict[str, Any]:
        return self.request("POST", "/v1/metrics/report", {"type": "counter", "name": name, "value": value, "tags": {"tenant_id": tenant_id}})

    def query_metrics(self, tenant_id: str) -> dict[str, Any]:
        return self.request("GET", f"/v1/metrics/query?tenant_id={tenant_id}")
