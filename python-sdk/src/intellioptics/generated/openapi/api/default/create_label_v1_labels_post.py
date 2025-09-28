"""Generated client for POST /v1/labels."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.label_create import LabelCreate
from ...models.label_record import LabelRecord
from ...types import Response


def _get_kwargs(*, body: LabelCreate) -> dict[str, Any]:
    headers: dict[str, Any] = {"Content-Type": "application/json"}
    return {
        "method": "post",
        "url": "/v1/labels",
        "headers": headers,
        "json": body.to_dict(),
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, LabelRecord]]:
    if response.status_code == HTTPStatus.OK:
        return LabelRecord.from_dict(response.json())
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        return HTTPValidationError.from_dict(response.json())
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HTTPValidationError, LabelRecord]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *, client: Union[AuthenticatedClient, Client], body: LabelCreate
) -> Response[Union[HTTPValidationError, LabelRecord]]:
    """Create Label"""

    response = client.get_httpx_client().request(**_get_kwargs(body=body))
    return _build_response(client=client, response=response)


def sync(
    *, client: Union[AuthenticatedClient, Client], body: LabelCreate
) -> Optional[Union[HTTPValidationError, LabelRecord]]:
    """Create Label"""

    return sync_detailed(client=client, body=body).parsed


async def asyncio_detailed(
    *, client: Union[AuthenticatedClient, Client], body: LabelCreate
) -> Response[Union[HTTPValidationError, LabelRecord]]:
    """Create Label"""

    response = await client.get_async_httpx_client().request(**_get_kwargs(body=body))
    return _build_response(client=client, response=response)


async def asyncio(
    *, client: Union[AuthenticatedClient, Client], body: LabelCreate
) -> Optional[Union[HTTPValidationError, LabelRecord]]:
    """Create Label"""

    return (await asyncio_detailed(client=client, body=body)).parsed
