from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.send_payment_reminders_api_v1_auto_payments_send_reminders_post_response_send_payment_reminders_api_v1_auto_payments_send_reminders_post import (
    SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost,
)
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auto-payments/send-reminders",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost
]:
    if response.status_code == 200:
        response_200 = SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost.from_dict(
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
    SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost
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
    SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost
]:
    """Send Payment Reminders

     Ручной запуск отправки напоминаний о предстоящих платежах.
    Полезно для тестирования.

    POST /api/v1/auto-payments/send-reminders

    Returns:
        Dict с результатами отправки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost]
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
    SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost
]:
    """Send Payment Reminders

     Ручной запуск отправки напоминаний о предстоящих платежах.
    Полезно для тестирования.

    POST /api/v1/auto-payments/send-reminders

    Returns:
        Dict с результатами отправки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost
]:
    """Send Payment Reminders

     Ручной запуск отправки напоминаний о предстоящих платежах.
    Полезно для тестирования.

    POST /api/v1/auto-payments/send-reminders

    Returns:
        Dict с результатами отправки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost
]:
    """Send Payment Reminders

     Ручной запуск отправки напоминаний о предстоящих платежах.
    Полезно для тестирования.

    POST /api/v1/auto-payments/send-reminders

    Returns:
        Dict с результатами отправки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SendPaymentRemindersApiV1AutoPaymentsSendRemindersPostResponseSendPaymentRemindersApiV1AutoPaymentsSendRemindersPost
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
