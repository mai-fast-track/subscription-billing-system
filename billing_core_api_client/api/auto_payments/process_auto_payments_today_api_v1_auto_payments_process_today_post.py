from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.process_auto_payments_today_api_v1_auto_payments_process_today_post_response_process_auto_payments_today_api_v1_auto_payments_process_today_post import (
    ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auto-payments/process-today",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost
]:
    if response.status_code == 200:
        response_200 = ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost.from_dict(
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
    ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost
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
    ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost
]:
    """Process Auto Payments Today

     Ручной запуск обработки автоплатежей для подписок, заканчивающихся сегодня.
    Использует новую архитектуру - запускает Celery задачу collect_subscriptions_for_payment.
    Полезно для тестирования.

    POST /api/v1/auto-payments/process-today

    Returns:
        Dict с task_id и результатом

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost]
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
    ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost
]:
    """Process Auto Payments Today

     Ручной запуск обработки автоплатежей для подписок, заканчивающихся сегодня.
    Использует новую архитектуру - запускает Celery задачу collect_subscriptions_for_payment.
    Полезно для тестирования.

    POST /api/v1/auto-payments/process-today

    Returns:
        Dict с task_id и результатом

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost
]:
    """Process Auto Payments Today

     Ручной запуск обработки автоплатежей для подписок, заканчивающихся сегодня.
    Использует новую архитектуру - запускает Celery задачу collect_subscriptions_for_payment.
    Полезно для тестирования.

    POST /api/v1/auto-payments/process-today

    Returns:
        Dict с task_id и результатом

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost
]:
    """Process Auto Payments Today

     Ручной запуск обработки автоплатежей для подписок, заканчивающихся сегодня.
    Использует новую архитектуру - запускает Celery задачу collect_subscriptions_for_payment.
    Полезно для тестирования.

    POST /api/v1/auto-payments/process-today

    Returns:
        Dict с task_id и результатом

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPostResponseProcessAutoPaymentsTodayApiV1AutoPaymentsProcessTodayPost
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
