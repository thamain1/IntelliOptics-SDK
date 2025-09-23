"""Custom exception hierarchy for the IntelliOptics SDK."""
from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional


class IntelliOpticsError(Exception):
    """Base class for all SDK errors."""


class ConfigurationError(IntelliOpticsError):
    """Raised when the SDK is misconfigured (e.g. missing endpoint)."""


class ApiTokenError(ConfigurationError):
    """Raised when an API token is missing or invalid."""


class TransportError(IntelliOpticsError):
    """Raised when an HTTP transport error occurs."""


class ApiError(IntelliOpticsError):
    """Base class for HTTP errors returned by the IntelliOptics API."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        payload: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = dict(payload or {})
        self.headers = dict(headers or {})


class ClientError(ApiError):
    """Represents generic 4xx responses."""


class AuthError(ClientError):
    """Raised for 401/403 style authentication failures."""


class NotFoundError(ClientError):
    """Raised when a requested resource is not found."""


class RateLimitError(ClientError):
    """Raised when the API indicates the client is rate limited."""


class ValidationError(ClientError):
    """Raised when the API reports validation problems (HTTP 422)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        payload: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        detail: Optional[Any] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            payload=payload,
            headers=headers,
        )
        self.detail = detail


class ServerError(ApiError):
    """Raised for 5xx server responses."""


def build_api_error(
    *,
    status_code: int,
    message: str,
    payload: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> ApiError:
    """Factory that maps HTTP status codes to concrete error classes."""
    if status_code in (401, 403):
        return AuthError(message, status_code=status_code, payload=payload, headers=headers)
    if status_code == 404:
        return NotFoundError(message, status_code=status_code, payload=payload, headers=headers)
    if status_code == 422:
        return ValidationError(
            message,
            status_code=status_code,
            payload=payload,
            headers=headers,
            detail=payload.get("detail") if isinstance(payload, MutableMapping) else None,
        )
    if status_code == 429:
        return RateLimitError(message, status_code=status_code, payload=payload, headers=headers)
    if 400 <= status_code < 500:
        return ClientError(message, status_code=status_code, payload=payload, headers=headers)
    return ServerError(message, status_code=status_code, payload=payload, headers=headers)
