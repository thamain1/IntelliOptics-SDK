"""Generated client for GET /v1/users/me."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.user_identity import UserIdentity
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    return {
        "method": "get",
        "url": "/v1/users/me",
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, UserIdentity]]:
    if response.status_code == HTTPStatus.OK:
        return UserIdentity.from_dict(response.json())
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        return HTTPValidationError.from_dict(response.json())
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HTTPValidationError, UserIdentity]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *, client: Union[AuthenticatedClient, Client]
) -> Response[Union[HTTPValidationError, UserIdentity]]:
    """Get Current User"""

    response = client.get_httpx_client().request(**_get_kwargs())
    return _build_response(client=client, response=response)


def sync(
    *, client: Union[AuthenticatedClient, Client]
) -> Optional[Union[HTTPValidationError, UserIdentity]]:
    """Get Current User"""

    return sync_detailed(client=client).parsed


async def asyncio_detailed(
    *, client: Union[AuthenticatedClient, Client]
) -> Response[Union[HTTPValidationError, UserIdentity]]:
    """Get Current User"""

    response = await client.get_async_httpx_client().request(**_get_kwargs())
    return _build_response(client=client, response=response)


async def asyncio(
    *, client: Union[AuthenticatedClient, Client]
) -> Optional[Union[HTTPValidationError, UserIdentity]]:
    """Get Current User"""

    return (await asyncio_detailed(client=client)).parsed
