from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.detector_out import DetectorOut
from ...models.http_validation_error import HTTPValidationError
from ...models.list_detectors_v1_detectors_get_response_200_type_1 import ListDetectorsV1DetectorsGetResponse200Type1
from typing import cast
from typing import cast, Union



def _get_kwargs(
    
) -> dict[str, Any]:
    

    

    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/v1/detectors",
    }


    return _kwargs



def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]]:
    if response.status_code == 200:
        def _parse_response_200(data: object) -> Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                response_200_type_0 = []
                _response_200_type_0 = data
                for response_200_type_0_item_data in (_response_200_type_0):
                    response_200_type_0_item = DetectorOut.from_dict(response_200_type_0_item_data)



                    response_200_type_0.append(response_200_type_0_item)

                return response_200_type_0
            except: # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = ListDetectorsV1DetectorsGetResponse200Type1.from_dict(data)



            return response_200_type_1

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],

) -> Response[Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]]:
    """ List Detectors

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]]
     """


    kwargs = _get_kwargs(
        
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: Union[AuthenticatedClient, Client],

) -> Optional[Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]]:
    """ List Detectors

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]
     """


    return sync_detailed(
        client=client,

    ).parsed

async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],

) -> Response[Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]]:
    """ List Detectors

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]]
     """


    kwargs = _get_kwargs(
        
    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],

) -> Optional[Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]]:
    """ List Detectors

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['ListDetectorsV1DetectorsGetResponse200Type1', list['DetectorOut']]]
     """


    return (await asyncio_detailed(
        client=client,

    )).parsed
