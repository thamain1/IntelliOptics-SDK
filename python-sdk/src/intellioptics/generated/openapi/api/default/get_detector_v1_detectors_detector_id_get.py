from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.detector_out import DetectorOut
from ...models.http_validation_error import HTTPValidationError
from typing import cast



def _get_kwargs(
    detector_id: str,

) -> dict[str, Any]:
    

    

    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/detectors/{detector_id}".format(detector_id=detector_id,),
    }


    return _kwargs



def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Union[DetectorOut, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = DetectorOut.from_dict(response.json())



        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Union[DetectorOut, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    detector_id: str,
    *,
    client: Union[AuthenticatedClient, Client],

) -> Response[Union[DetectorOut, HTTPValidationError]]:
    """ Get Detector

    Args:
        detector_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetectorOut, HTTPValidationError]]
     """


    kwargs = _get_kwargs(
        detector_id=detector_id,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    detector_id: str,
    *,
    client: Union[AuthenticatedClient, Client],

) -> Optional[Union[DetectorOut, HTTPValidationError]]:
    """ Get Detector

    Args:
        detector_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetectorOut, HTTPValidationError]
     """


    return sync_detailed(
        detector_id=detector_id,
client=client,

    ).parsed

async def asyncio_detailed(
    detector_id: str,
    *,
    client: Union[AuthenticatedClient, Client],

) -> Response[Union[DetectorOut, HTTPValidationError]]:
    """ Get Detector

    Args:
        detector_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetectorOut, HTTPValidationError]]
     """


    kwargs = _get_kwargs(
        detector_id=detector_id,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    detector_id: str,
    *,
    client: Union[AuthenticatedClient, Client],

) -> Optional[Union[DetectorOut, HTTPValidationError]]:
    """ Get Detector

    Args:
        detector_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetectorOut, HTTPValidationError]
     """


    return (await asyncio_detailed(
        detector_id=detector_id,
client=client,

    )).parsed
