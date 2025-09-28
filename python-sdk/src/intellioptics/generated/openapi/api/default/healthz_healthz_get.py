from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...models.healthz_healthz_get_response_200_type_0 import HealthzHealthzGetResponse200Type0
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/healthz",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[HTTPValidationError, Union["HealthzHealthzGetResponse200Type0", str]]:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Union["HealthzHealthzGetResponse200Type0", str]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = HealthzHealthzGetResponse200Type0.from_dict(data)

                return response_200_type_0
            except:  # noqa: E722
                pass
            return cast(Union["HealthzHealthzGetResponse200Type0", str], data)

        response_200 = _parse_response_200(response.json())

        return response_200

    response_default = HTTPValidationError.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HTTPValidationError, Union["HealthzHealthzGetResponse200Type0", str]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[HTTPValidationError, Union["HealthzHealthzGetResponse200Type0", str]]]:
    """Health check

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['HealthzHealthzGetResponse200Type0', str]]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[HTTPValidationError, Union["HealthzHealthzGetResponse200Type0", str]]]:
    """Health check

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['HealthzHealthzGetResponse200Type0', str]]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[HTTPValidationError, Union["HealthzHealthzGetResponse200Type0", str]]]:
    """Health check

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['HealthzHealthzGetResponse200Type0', str]]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[HTTPValidationError, Union["HealthzHealthzGetResponse200Type0", str]]]:
    """Health check

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['HealthzHealthzGetResponse200Type0', str]]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
