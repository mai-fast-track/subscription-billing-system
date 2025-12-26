from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_subscriptions_ending_tomorrow_api_v1_auto_payments_subscriptions_ending_tomorrow_get_response_200_item import (
    GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/auto-payments/subscriptions-ending-tomorrow",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = (
                GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item.from_dict(
                    response_200_item_data
                )
            )

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[list["GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item"]]:
    """Get Subscriptions Ending Tomorrow

     Получить список подписок, которые заканчиваются завтра.
    Полезно для проверки перед отправкой напоминаний.

    GET /api/v1/auto-payments/subscriptions-ending-tomorrow

    Returns:
        List подписок с информацией

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item']]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[list["GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item"]]:
    """Get Subscriptions Ending Tomorrow

     Получить список подписок, которые заканчиваются завтра.
    Полезно для проверки перед отправкой напоминаний.

    GET /api/v1/auto-payments/subscriptions-ending-tomorrow

    Returns:
        List подписок с информацией

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item']
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[list["GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item"]]:
    """Get Subscriptions Ending Tomorrow

     Получить список подписок, которые заканчиваются завтра.
    Полезно для проверки перед отправкой напоминаний.

    GET /api/v1/auto-payments/subscriptions-ending-tomorrow

    Returns:
        List подписок с информацией

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item']]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[list["GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item"]]:
    """Get Subscriptions Ending Tomorrow

     Получить список подписок, которые заканчиваются завтра.
    Полезно для проверки перед отправкой напоминаний.

    GET /api/v1/auto-payments/subscriptions-ending-tomorrow

    Returns:
        List подписок с информацией

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['GetSubscriptionsEndingTomorrowApiV1AutoPaymentsSubscriptionsEndingTomorrowGetResponse200Item']
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
