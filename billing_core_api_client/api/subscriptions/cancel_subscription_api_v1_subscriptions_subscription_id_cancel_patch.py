from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cancel_subscription_request import CancelSubscriptionRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.subscription_response import SubscriptionResponse
from ...types import Response


def _get_kwargs(
    subscription_id: int,
    *,
    body: CancelSubscriptionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/api/v1/subscriptions/{subscription_id}/cancel",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, SubscriptionResponse]]:
    if response.status_code == 200:
        response_200 = SubscriptionResponse.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, SubscriptionResponse]]:
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
    body: CancelSubscriptionRequest,
) -> Response[Union[HTTPValidationError, SubscriptionResponse]]:
    """Cancel Subscription

     Отменить подписку

    Query параметры:
    - with_refund=False (по умолчанию): Отмена без возврата, подписка активна до end_date
    - with_refund=True: Отмена с возвратом, подписка отменяется сразу

    Args:
        subscription_id (int):
        body (CancelSubscriptionRequest): Схема запроса на отмену подписки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, SubscriptionResponse]]
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
    body: CancelSubscriptionRequest,
) -> Optional[Union[HTTPValidationError, SubscriptionResponse]]:
    """Cancel Subscription

     Отменить подписку

    Query параметры:
    - with_refund=False (по умолчанию): Отмена без возврата, подписка активна до end_date
    - with_refund=True: Отмена с возвратом, подписка отменяется сразу

    Args:
        subscription_id (int):
        body (CancelSubscriptionRequest): Схема запроса на отмену подписки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, SubscriptionResponse]
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
    body: CancelSubscriptionRequest,
) -> Response[Union[HTTPValidationError, SubscriptionResponse]]:
    """Cancel Subscription

     Отменить подписку

    Query параметры:
    - with_refund=False (по умолчанию): Отмена без возврата, подписка активна до end_date
    - with_refund=True: Отмена с возвратом, подписка отменяется сразу

    Args:
        subscription_id (int):
        body (CancelSubscriptionRequest): Схема запроса на отмену подписки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, SubscriptionResponse]]
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
    body: CancelSubscriptionRequest,
) -> Optional[Union[HTTPValidationError, SubscriptionResponse]]:
    """Cancel Subscription

     Отменить подписку

    Query параметры:
    - with_refund=False (по умолчанию): Отмена без возврата, подписка активна до end_date
    - with_refund=True: Отмена с возвратом, подписка отменяется сразу

    Args:
        subscription_id (int):
        body (CancelSubscriptionRequest): Схема запроса на отмену подписки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, SubscriptionResponse]
    """

    return (
        await asyncio_detailed(
            subscription_id=subscription_id,
            client=client,
            body=body,
        )
    ).parsed
