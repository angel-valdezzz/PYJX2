from __future__ import annotations

from typing import Any, Optional

import requests

from ..config.settings import JiraSettings
from ..security.encryption import SymmetricEncryptionService


class JiraClient:
    """Low-level Jira REST API client."""

    def __init__(self, settings: JiraSettings, timeout: float = 30.0) -> None:
        self._base_url = settings.url.rstrip("/")
        enc_service = SymmetricEncryptionService()
        self._auth = (settings.username, enc_service.decrypt(settings.password))
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self._base_url}/rest/api/3/{path.lstrip('/')}"

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        resp = requests.get(
            self._url(path), headers=self._headers, auth=self._auth, params=params, timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, data: dict) -> Any:
        resp = requests.post(
            self._url(path), headers=self._headers, auth=self._auth, json=data, timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()

    def put(self, path: str, data: dict) -> Any:
        resp = requests.put(
            self._url(path), headers=self._headers, auth=self._auth, json=data, timeout=self._timeout
        )
        resp.raise_for_status()
        return resp.json()

    def get_issue(self, key: str) -> dict:
        return self.get(f"issue/{key}")

    def create_issue(self, fields: dict) -> dict:
        return self.post("issue", {"fields": fields})

    def update_issue(self, key: str, fields: dict) -> None:
        resp = requests.put(
            self._url(f"issue/{key}"),
            headers=self._headers,
            auth=self._auth,
            json={"fields": fields},
            timeout=self._timeout,
        )
        resp.raise_for_status()

    def add_link(self, issue_key: str, linked_issue_key: str, link_type: str = "Test") -> dict:
        return self.post("issueLink", {
            "type": {"name": link_type},
            "inwardIssue": {"key": issue_key},
            "outwardIssue": {"key": linked_issue_key},
        })

    def search_issues(self, jql: str, fields: Optional[list[str]] = None, max_results: int = 100) -> list[dict]:
        payload: dict = {"jql": jql, "maxResults": max_results}
        if fields:
            payload["fields"] = fields
        result = self.post("search", payload)
        return result.get("issues", [])
