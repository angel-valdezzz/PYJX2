from __future__ import annotations

from typing import Any, Optional

import httpx

from ..config.settings import XraySettings


class XrayClient:
    """Low-level Xray Cloud REST API client with automatic token refresh."""

    GRAPHQL_URL = "https://xray.cloud.getxray.app/api/v2/graphql"

    def __init__(self, settings: XraySettings, timeout: float = 30.0) -> None:
        self._client_id = settings.client_id
        self._client_secret = settings.client_secret
        self._base_url = settings.base_url.rstrip("/")
        self._timeout = timeout
        self._token: Optional[str] = None

    def _authenticate(self) -> str:
        url = f"{self._base_url}/authenticate"
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                url,
                json={"client_id": self._client_id, "client_secret": self._client_secret},
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            token = resp.text.strip('"')
            self._token = token
            return token

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
        with httpx.Client(headers=self._headers(), timeout=self._timeout) as client:
            resp = getattr(client, method)(url, **kwargs)
            if resp.status_code == 401:
                self._token = None
                resp = getattr(
                    httpx.Client(headers=self._headers(), timeout=self._timeout),
                    method,
                )(url, **kwargs)
            resp.raise_for_status()
            if resp.content:
                return resp.json()
            return None

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("get", path, params=params)

    def post(self, path: str, data: Optional[dict] = None) -> Any:
        return self._request("post", path, json=data)

    def put(self, path: str, data: Optional[dict] = None) -> Any:
        return self._request("put", path, json=data)

    def graphql(self, query: str, variables: Optional[dict] = None) -> dict:
        with httpx.Client(headers=self._headers(), timeout=self._timeout) as client:
            resp = client.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": variables or {}},
            )
            resp.raise_for_status()
            result = resp.json()
            if "errors" in result:
                raise RuntimeError(f"GraphQL errors: {result['errors']}")
            return result.get("data", {})

    def upload_file(self, path: str, file_path: str) -> Any:
        url = f"{self._base_url}/{path.lstrip('/')}"
        with open(file_path, "rb") as f:
            content = f.read()
        import mimetypes
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self._get_token()}",
                },
                files={"file": (file_path, content, mime_type)},
            )
            resp.raise_for_status()
            return resp.json() if resp.content else None
