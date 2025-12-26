from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_auto_payment_stats_api_v1_auto_payments_stats_get_response_get_auto_payment_stats_api_v1_auto_payments_stats_get import (
    GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/auto-payments/stats",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet]:
    if response.status_code == 200:
        response_200 = (
            GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet.from_dict(
                response.json()
            )
        )

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet]:
    """Get Auto Payment Stats

     Получить статистику по автоплатежам.

    GET /api/v1/auto-payments/stats

    Returns:
        Dict со статистикой

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet]:
    """Get Auto Payment Stats

     Получить статистику по автоплатежам.

    GET /api/v1/auto-payments/stats

    Returns:
        Dict со статистикой

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet]:
    """Get Auto Payment Stats

     Получить статистику по автоплатежам.

    GET /api/v1/auto-payments/stats

    Returns:
        Dict со статистикой

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet]:
    """Get Auto Payment Stats

     Получить статистику по автоплатежам.

    GET /api/v1/auto-payments/stats

    Returns:
        Dict со статистикой

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAutoPaymentStatsApiV1AutoPaymentsStatsGetResponseGetAutoPaymentStatsApiV1AutoPaymentsStatsGet
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
