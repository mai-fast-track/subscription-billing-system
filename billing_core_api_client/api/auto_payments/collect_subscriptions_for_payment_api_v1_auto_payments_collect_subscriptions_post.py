from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.collect_subscriptions_for_payment_api_v1_auto_payments_collect_subscriptions_post_response_collect_subscriptions_for_payment_api_v1_auto_payments_collect_subscriptions_post import (
    CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auto-payments/collect-subscriptions",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost
]:
    if response.status_code == 200:
        response_200 = CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost.from_dict(
            response.json()
        )

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost
]:
    """Collect Subscriptions For Payment

     Ручной запуск сбора подписок для обработки (новая архитектура).
    Запускает Celery задачу collect_subscriptions_for_payment.

    POST /api/v1/auto-payments/collect-subscriptions

    Returns:
        Dict с task_id и результатом

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost
]:
    """Collect Subscriptions For Payment

     Ручной запуск сбора подписок для обработки (новая архитектура).
    Запускает Celery задачу collect_subscriptions_for_payment.

    POST /api/v1/auto-payments/collect-subscriptions

    Returns:
        Dict с task_id и результатом

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost
]:
    """Collect Subscriptions For Payment

     Ручной запуск сбора подписок для обработки (новая архитектура).
    Запускает Celery задачу collect_subscriptions_for_payment.

    POST /api/v1/auto-payments/collect-subscriptions

    Returns:
        Dict с task_id и результатом

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost
]:
    """Collect Subscriptions For Payment

     Ручной запуск сбора подписок для обработки (новая архитектура).
    Запускает Celery задачу collect_subscriptions_for_payment.

    POST /api/v1/auto-payments/collect-subscriptions

    Returns:
        Dict с task_id и результатом

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPostResponseCollectSubscriptionsForPaymentApiV1AutoPaymentsCollectSubscriptionsPost
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
