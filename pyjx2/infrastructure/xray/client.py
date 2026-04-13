from __future__ import annotations

import mimetypes
from typing import Any, Optional

import requests

from ..config.settings import XraySettings


class XrayClient:
    """Low-level Xray Cloud REST API client with automatic token refresh."""

    def __init__(self, settings: XraySettings, timeout: float = 30.0) -> None:
        self._client_id = settings.client_id
        self._client_secret = settings.client_secret
        self._base_url = settings.base_url.rstrip("/")
        self._graphql_url = settings.graphql_url.rstrip("/")
        self._timeout = timeout
        self._token: Optional[str] = None

    def _authenticate(self) -> str:
        url = f"{self._base_url}/authenticate"
        resp = requests.post(
            url,
            json={"client_id": self._client_id, "client_secret": self._client_secret},
            headers={"Content-Type": "application/json"},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        self._token = resp.text.strip('"')
        return self._token

    def _get_token(self) -> str:
        if not self._token:
            return self._authenticate()
        return self._token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        resp = requests.request(method.upper(), url, headers=self._headers(), timeout=self._timeout, **kwargs)
        if resp.status_code == 401:
            self._token = None
            resp = requests.request(method.upper(), url, headers=self._headers(), timeout=self._timeout, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("get", path, params=params)

    def post(self, path: str, data: Optional[dict] = None) -> Any:
        return self._request("post", path, json=data)

    def put(self, path: str, data: Optional[dict] = None) -> Any:
        return self._request("put", path, json=data)

    def delete(self, path: str) -> Any:
        return self._request("delete", path)

    def graphql(self, query: str, variables: Optional[dict] = None) -> dict:
        resp = requests.post(
            self._graphql_url,
            headers=self._headers(),
            json={"query": query, "variables": variables or {}},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise RuntimeError(f"GraphQL errors: {result['errors']}")
        return result.get("data", {})

    def upload_file(self, path: str, file_path: str) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {self._get_token()}"},
                files={"file": (file_path, f, mime_type)},
                timeout=self._timeout,
            )
        resp.raise_for_status()
        return resp.json() if resp.content else None
