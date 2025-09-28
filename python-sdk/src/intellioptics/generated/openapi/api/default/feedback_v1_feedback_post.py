from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ...client import AuthenticatedClient, Client
from ...models.feedback_in import FeedbackIn
from ...models.feedback_v1_feedback_post_response_200 import FeedbackV1FeedbackPostResponse200
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: FeedbackIn,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/feedback",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]:
    if response.status_code == 200:
        response_200 = FeedbackV1FeedbackPostResponse200.from_dict(response.json())

        return response_200

    response_default = HTTPValidationError.from_dict(response.json())

    return response_default


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: FeedbackIn,
) -> Response[Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]]:
    """Submit feedback

    Args:
        body (FeedbackIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: FeedbackIn,
) -> Optional[Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]]:
    """Submit feedback

    Args:
        body (FeedbackIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: FeedbackIn,
) -> Response[Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]]:
    """Submit feedback

    Args:
        body (FeedbackIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: FeedbackIn,
) -> Optional[Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]]:
    """Submit feedback

    Args:
        body (FeedbackIn):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[FeedbackV1FeedbackPostResponse200, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
