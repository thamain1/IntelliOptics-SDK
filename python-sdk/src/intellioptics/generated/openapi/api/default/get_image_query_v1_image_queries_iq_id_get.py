from http import HTTPStatus

from typing import Any, Dict, Optional, Union

from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.answer_out import AnswerOut
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    iq_id: str,

) -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/v1/image-queries/{iq_id}".format(
            iq_id=iq_id,
        ),
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/v1/image-queries/{iq_id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[AnswerOut, HTTPValidationError]]:

    if response.status_code == HTTPStatus.OK:

    if response.status_code == 200:

        response_200 = AnswerOut.from_dict(response.json())

        return response_200
    if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[AnswerOut, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    iq_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[AnswerOut, HTTPValidationError]]:
    """Get Image Query

    Args:
        iq_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AnswerOut, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iq_id=iq_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    iq_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[AnswerOut, HTTPValidationError]]:
    """Get Image Query

    Args:
        iq_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AnswerOut, HTTPValidationError]
    """

    return sync_detailed(
        iq_id=iq_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    iq_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[AnswerOut, HTTPValidationError]]:
    """Get Image Query

    Args:
        iq_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AnswerOut, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        iq_id=iq_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    iq_id: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[AnswerOut, HTTPValidationError]]:
    """Get Image Query

    Args:
        iq_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AnswerOut, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            iq_id=iq_id,
            client=client,
        )
    ).parsed
