"""Generated client for GET /v1/detectors."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.detector_list import DetectorList
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    return {
        "method": "get",
        "url": "/v1/detectors",
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[DetectorList, HTTPValidationError]]:
    if response.status_code == HTTPStatus.OK:
        return DetectorList.from_dict(response.json())
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        return HTTPValidationError.from_dict(response.json())
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[DetectorList, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *, client: Union[AuthenticatedClient, Client]
) -> Response[Union[DetectorList, HTTPValidationError]]:
    """List Detectors"""

    response = client.get_httpx_client().request(**_get_kwargs())
    return _build_response(client=client, response=response)


def sync(
    *, client: Union[AuthenticatedClient, Client]
) -> Optional[Union[DetectorList, HTTPValidationError]]:
    """List Detectors"""

    return sync_detailed(client=client).parsed


async def asyncio_detailed(
    *, client: Union[AuthenticatedClient, Client]
) -> Response[Union[DetectorList, HTTPValidationError]]:
    """List Detectors"""

    response = await client.get_async_httpx_client().request(**_get_kwargs())
    return _build_response(client=client, response=response)


async def asyncio(
    *, client: Union[AuthenticatedClient, Client]
) -> Optional[Union[DetectorList, HTTPValidationError]]:
    """List Detectors"""

    return (await asyncio_detailed(client=client)).parsed
