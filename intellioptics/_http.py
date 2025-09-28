"""HTTP helpers for the IntelliOptics SDK."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping

import httpx
import requests

from .errors import IntelliOpticsClientError


_DEFAULT_TIMEOUT = 30.0


def _build_url(base: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return f"{base.rstrip('/')}{path}"


class HttpClient:
    """Synchronous HTTP wrapper around :mod:`requests`."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        *,
        verify: bool = True,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not base_url:
            raise IntelliOpticsClientError("Missing INTELLIOPTICS_ENDPOINT")

        self.base = base_url.rstrip("/")
        self.verify = verify
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {api_token}"})
        self.headers = self._session.headers

    # ------------------------------------------------------------------
    # Low level helpers
    # ------------------------------------------------------------------
    def _merge_headers(self, headers: Mapping[str, str] | None) -> MutableMapping[str, str]:
        combined: MutableMapping[str, str] = dict(self._session.headers)
        if headers:
            combined.update(headers)
        return combined

    def request_raw(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        url = _build_url(self.base, path)
        response = self._session.request(
            method.upper(),
            url,
            timeout=self.timeout,
            verify=self.verify,
            headers=self._merge_headers(headers),
            **kwargs,
        )

        if not response.ok:
            content = response.text.strip()
            raise IntelliOpticsClientError(
                f"{method.upper()} {path} failed with {response.status_code}: {content or 'no body'}"
            )

        return response

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.request_raw(method, path, **kwargs)

        if response.status_code == 204 or not response.content:
            return {}

        content_type = response.headers.get("Content-Type", "").lower()
        if "json" in content_type:
            return response.json()
        return response.text

    # ------------------------------------------------------------------
    # Convenience JSON helpers
    # ------------------------------------------------------------------
    def get_json(self, path: str, *, params: Mapping[str, Any] | None = None, **kwargs: Any) -> Any:
        return self._request("GET", path, params=params, **kwargs)

    def post_json(self, path: str, **kwargs: Any) -> Any:
        return self._request("POST", path, **kwargs)

    def put_json(self, path: str, **kwargs: Any) -> Any:
        return self._request("PUT", path, **kwargs)

    def patch_json(self, path: str, **kwargs: Any) -> Any:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Any:
        return self._request("DELETE", path, **kwargs)

    def close(self) -> None:
        self._session.close()


class AsyncHttpClient:
    """Async counterpart implemented with :mod:`httpx`."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        *,
        verify: bool = True,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not base_url:
            raise IntelliOpticsClientError("Missing INTELLIOPTICS_ENDPOINT")

        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            verify=verify,
            headers={"Authorization": f"Bearer {api_token}"},
        )

    async def _merge_headers(self, headers: Mapping[str, str] | None) -> MutableMapping[str, str]:
        combined: MutableMapping[str, str] = dict(self._client.headers)
        if headers:
            combined.update(headers)
        return combined

    async def request_raw(
        self,
        method: str,
        path: str,
        *,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        response = await self._client.request(
            method.upper(),
            path,
            headers=await self._merge_headers(headers),
            **kwargs,
        )

        if not response.is_success:
            content = response.text.strip()
            raise IntelliOpticsClientError(
                f"{method.upper()} {path} failed with {response.status_code}: {content or 'no body'}"
            )

        return response

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = await self.request_raw(method, path, **kwargs)

        if response.status_code == 204 or not response.content:
            return {}

        content_type = response.headers.get("Content-Type", "").lower()
        if "json" in content_type:
            return response.json()
        return response.text

    async def get_json(
        self, path: str, *, params: Mapping[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        return await self._request("GET", path, params=params, **kwargs)

    async def post_json(self, path: str, **kwargs: Any) -> Any:
        return await self._request("POST", path, **kwargs)

    async def put_json(self, path: str, **kwargs: Any) -> Any:
        return await self._request("PUT", path, **kwargs)

    async def patch_json(self, path: str, **kwargs: Any) -> Any:
        return await self._request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Any:
        return await self._request("DELETE", path, **kwargs)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":  # pragma: no cover - passthrough
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - passthrough
        await self.close()

