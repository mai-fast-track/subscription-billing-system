from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.apply_promotion_request import ApplyPromotionRequest
from ...models.apply_promotion_response import ApplyPromotionResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    subscription_id: int,
    *,
    body: ApplyPromotionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/subscriptions/{subscription_id}/apply-promotion",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ApplyPromotionResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = ApplyPromotionResponse.from_dict(response.json())

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ApplyPromotionResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    subscription_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ApplyPromotionRequest,
) -> Response[Union[ApplyPromotionResponse, HTTPValidationError]]:
    """Apply Promotion To Subscription

     Применить промокод к активной подписке (продлевает end_date на бонусные дни)

    Args:
        subscription_id (int):
        body (ApplyPromotionRequest): Схема запроса для применения промокода к активной подписке

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ApplyPromotionResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        subscription_id=subscription_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    subscription_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ApplyPromotionRequest,
) -> Optional[Union[ApplyPromotionResponse, HTTPValidationError]]:
    """Apply Promotion To Subscription

     Применить промокод к активной подписке (продлевает end_date на бонусные дни)

    Args:
        subscription_id (int):
        body (ApplyPromotionRequest): Схема запроса для применения промокода к активной подписке

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ApplyPromotionResponse, HTTPValidationError]
    """

    return sync_detailed(
        subscription_id=subscription_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    subscription_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ApplyPromotionRequest,
) -> Response[Union[ApplyPromotionResponse, HTTPValidationError]]:
    """Apply Promotion To Subscription

     Применить промокод к активной подписке (продлевает end_date на бонусные дни)

    Args:
        subscription_id (int):
        body (ApplyPromotionRequest): Схема запроса для применения промокода к активной подписке

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ApplyPromotionResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        subscription_id=subscription_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    subscription_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: ApplyPromotionRequest,
) -> Optional[Union[ApplyPromotionResponse, HTTPValidationError]]:
    """Apply Promotion To Subscription

     Применить промокод к активной подписке (продлевает end_date на бонусные дни)

    Args:
        subscription_id (int):
        body (ApplyPromotionRequest): Схема запроса для применения промокода к активной подписке

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ApplyPromotionResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            subscription_id=subscription_id,
            client=client,
            body=body,
        )
    ).parsed
