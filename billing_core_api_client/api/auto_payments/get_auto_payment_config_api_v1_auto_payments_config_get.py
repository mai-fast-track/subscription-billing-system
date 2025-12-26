from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_auto_payment_config_api_v1_auto_payments_config_get_response_get_auto_payment_config_api_v1_auto_payments_config_get import (
    GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/auto-payments/config",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet]:
    if response.status_code == 200:
        response_200 = GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet.from_dict(
            response.json()
        )

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet]:
    """Get Auto Payment Config

     Получить текущие настройки автоплатежей.

    GET /api/v1/auto-payments/config

    Returns:
        Dict с текущими настройками

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet]:
    """Get Auto Payment Config

     Получить текущие настройки автоплатежей.

    GET /api/v1/auto-payments/config

    Returns:
        Dict с текущими настройками

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet]:
    """Get Auto Payment Config

     Получить текущие настройки автоплатежей.

    GET /api/v1/auto-payments/config

    Returns:
        Dict с текущими настройками

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet]:
    """Get Auto Payment Config

     Получить текущие настройки автоплатежей.

    GET /api/v1/auto-payments/config

    Returns:
        Dict с текущими настройками

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetAutoPaymentConfigApiV1AutoPaymentsConfigGetResponseGetAutoPaymentConfigApiV1AutoPaymentsConfigGet
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
