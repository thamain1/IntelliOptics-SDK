"""HTTP utilities shared across the IntelliOptics SDK."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx

from .errors import (
    ApiError,
    ApiTokenError,
    ConfigurationError,
    TransportError,
    build_api_error,
)

_USER_AGENT = "intellioptics-sdk"


def _json_from_response(response: httpx.Response) -> Any:
    if response.status_code == 204:
        return None
    try:
        return response.json()
    except json.JSONDecodeError as exc:  # pragma: no cover - should not happen in healthy API
        raise ApiError(
            "Response from IntelliOptics API was not valid JSON",
            status_code=response.status_code,
            payload={"body": response.text},
            headers=response.headers,
        ) from exc


class HttpClient:
    """Thin wrapper around :class:`httpx.Client` that raises SDK errors."""

    def __init__(
        self,
        *,
        base_url: Optional[str],
        api_token: Optional[str],
        verify: bool = True,
        timeout: float = 30.0,
    ) -> None:
        if not api_token:
            raise ApiTokenError("Missing INTELLIOPTICS_API_TOKEN")
        if not base_url:
            raise ConfigurationError("Missing INTELLIOPTICS_ENDPOINT")

        headers = {"Authorization": f"Bearer {api_token}", "User-Agent": _USER_AGENT}
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(timeout),
            verify=verify,
        )

    def close(self) -> None:
        self._client.close()

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise TransportError("Request to IntelliOptics API timed out") from exc
        except httpx.HTTPError as exc:
            raise TransportError("HTTP transport error communicating with IntelliOptics API") from exc

        if response.is_success:
            return response

        payload: Dict[str, Any]
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = {"body": response.text}

        message = payload.get("detail") if isinstance(payload, dict) else None
        if not message:
            message = f"HTTP {response.status_code} error from IntelliOptics API"

        raise build_api_error(
            status_code=response.status_code,
            message=str(message),
            payload=payload,
            headers=dict(response.headers),
        )

    def get_json(self, path: str, **kwargs: Any) -> Any:
        response = self.request("GET", path, **kwargs)
        return _json_from_response(response)

    def post_json(self, path: str, **kwargs: Any) -> Any:
        response = self.request("POST", path, **kwargs)
        return _json_from_response(response)

    def delete_json(self, path: str, **kwargs: Any) -> Any:
        response = self.request("DELETE", path, **kwargs)
        return _json_from_response(response)
