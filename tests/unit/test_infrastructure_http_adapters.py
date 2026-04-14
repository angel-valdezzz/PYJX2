from __future__ import annotations

from pyjx2.infrastructure.config.settings import JiraSettings, XraySettings
from pyjx2.infrastructure.jira.client import JiraClient
from pyjx2.infrastructure.xray.client import XrayClient


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        json_data=None,
        text: str = "",
        content: bytes | None = None,
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self.content = content if content is not None else (b"" if json_data is None else b"{}")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


def test_jira_client_create_issue_posts_expected_payload(monkeypatch):
    calls: list[dict] = []

    def fake_post(url, headers, auth, json, timeout):
        calls.append(
            {
                "url": url,
                "headers": headers,
                "auth": auth,
                "json": json,
                "timeout": timeout,
            }
        )
        return _FakeResponse(json_data={"key": "PROJ-10", "id": "10010"})

    monkeypatch.setattr("pyjx2.infrastructure.jira.client.requests.post", fake_post)

    client = JiraClient(JiraSettings(username="user@example.com", password="plain_token", env="QA"))
    result = client.create_issue(
        {
            "project": {"key": "PROJ"},
            "issuetype": {"name": "Test"},
            "summary": "Login flow",
        }
    )

    assert result["key"] == "PROJ-10"
    assert calls[0]["url"].endswith("/rest/api/3/issue")
    assert calls[0]["auth"] == ("user@example.com", "plain_token")
    assert calls[0]["json"]["fields"]["summary"] == "Login flow"


def test_xray_client_retries_once_after_401(monkeypatch):
    auth_calls: list[dict] = []
    request_headers: list[str] = []
    responses = iter(
        [
            _FakeResponse(
                status_code=401, json_data={"error": "expired"}, content=b'{"error":"expired"}'
            ),
            _FakeResponse(status_code=200, json_data={"ok": True}, content=b'{"ok": true}'),
        ]
    )

    def fake_post(url, json, headers, timeout):
        auth_calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        token = f"token-{len(auth_calls)}"
        return _FakeResponse(text=f'"{token}"', content=f'"{token}"'.encode())

    def fake_request(method, url, headers, timeout, **kwargs):
        request_headers.append(headers["Authorization"])
        return next(responses)

    monkeypatch.setattr("pyjx2.infrastructure.xray.client.requests.post", fake_post)
    monkeypatch.setattr("pyjx2.infrastructure.xray.client.requests.request", fake_request)

    client = XrayClient(
        XraySettings(
            client_id="client-id",
            client_secret="client-secret",
            env="QA",
        )
    )

    result = client.get("testexec/100/test")

    assert result == {"ok": True}
    assert len(auth_calls) == 2
    assert request_headers == ["Bearer token-1", "Bearer token-2"]
