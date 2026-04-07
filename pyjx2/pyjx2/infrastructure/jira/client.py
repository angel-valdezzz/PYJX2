from __future__ import annotations

import base64
from typing import Any, Optional

import httpx

from ..config.settings import JiraSettings


class JiraClient:
    """Low-level Jira REST API client."""

    def __init__(self, settings: JiraSettings, timeout: float = 30.0) -> None:
        self._base_url = settings.url.rstrip("/")
        credentials = f"{settings.username}:{settings.api_token}"
        token = base64.b64encode(credentials.encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self._base_url}/rest/api/3/{path.lstrip('/')}"

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        with httpx.Client(headers=self._headers, timeout=self._timeout) as client:
            resp = client.get(self._url(path), params=params)
            resp.raise_for_status()
            return resp.json()

    def post(self, path: str, data: dict) -> Any:
        with httpx.Client(headers=self._headers, timeout=self._timeout) as client:
            resp = client.post(self._url(path), json=data)
            resp.raise_for_status()
            return resp.json()

    def put(self, path: str, data: dict) -> Any:
        with httpx.Client(headers=self._headers, timeout=self._timeout) as client:
            resp = client.put(self._url(path), json=data)
            resp.raise_for_status()
            return resp.json()

    def get_issue(self, key: str) -> dict:
        return self.get(f"issue/{key}")

    def create_issue(self, fields: dict) -> dict:
        return self.post("issue", {"fields": fields})

    def update_issue(self, key: str, fields: dict) -> None:
        with httpx.Client(headers=self._headers, timeout=self._timeout) as client:
            resp = client.put(self._url(f"issue/{key}"), json={"fields": fields})
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
