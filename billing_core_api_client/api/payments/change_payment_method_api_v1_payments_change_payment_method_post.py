from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.change_payment_method_request import ChangePaymentMethodRequest
from ...models.http_validation_error import HTTPValidationError
from ...models.payment_create_response import PaymentCreateResponse
from ...types import Response


def _get_kwargs(
    *,
    body: ChangePaymentMethodRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/payments/change-payment-method",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, PaymentCreateResponse]]:
    if response.status_code == 200:
        response_200 = PaymentCreateResponse.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, PaymentCreateResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ChangePaymentMethodRequest,
) -> Response[Union[HTTPValidationError, PaymentCreateResponse]]:
    r"""Change Payment Method

     Endpoint: Смена карты для автосписаний

    Создает платеж с минимальной суммой (по умолчанию 1 рубль) для привязки новой карты.
    После успешной оплаты новая карта будет использоваться для автосписаний.

    POST /api/v1/payments/change-payment-method
    {
        \"user_id\": 1,
        \"return_url\": \"https://yourdomain.com/payment/success\",
        \"amount\": 1.0
    }

    Response:
    {
        \"success\": true,
        \"message\": \"Платеж создан для привязки новой карты. После успешной оплаты карта будет
    обновлена.\",
        \"confirmation_url\": \"https://yookassa.ru/payments/...\",
        \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\"
    }

    Args:
        body (ChangePaymentMethodRequest): Запрос на смену карты для автосписаний

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, PaymentCreateResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ChangePaymentMethodRequest,
) -> Optional[Union[HTTPValidationError, PaymentCreateResponse]]:
    r"""Change Payment Method

     Endpoint: Смена карты для автосписаний

    Создает платеж с минимальной суммой (по умолчанию 1 рубль) для привязки новой карты.
    После успешной оплаты новая карта будет использоваться для автосписаний.

    POST /api/v1/payments/change-payment-method
    {
        \"user_id\": 1,
        \"return_url\": \"https://yourdomain.com/payment/success\",
        \"amount\": 1.0
    }

    Response:
    {
        \"success\": true,
        \"message\": \"Платеж создан для привязки новой карты. После успешной оплаты карта будет
    обновлена.\",
        \"confirmation_url\": \"https://yookassa.ru/payments/...\",
        \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\"
    }

    Args:
        body (ChangePaymentMethodRequest): Запрос на смену карты для автосписаний

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, PaymentCreateResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ChangePaymentMethodRequest,
) -> Response[Union[HTTPValidationError, PaymentCreateResponse]]:
    r"""Change Payment Method

     Endpoint: Смена карты для автосписаний

    Создает платеж с минимальной суммой (по умолчанию 1 рубль) для привязки новой карты.
    После успешной оплаты новая карта будет использоваться для автосписаний.

    POST /api/v1/payments/change-payment-method
    {
        \"user_id\": 1,
        \"return_url\": \"https://yourdomain.com/payment/success\",
        \"amount\": 1.0
    }

    Response:
    {
        \"success\": true,
        \"message\": \"Платеж создан для привязки новой карты. После успешной оплаты карта будет
    обновлена.\",
        \"confirmation_url\": \"https://yookassa.ru/payments/...\",
        \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\"
    }

    Args:
        body (ChangePaymentMethodRequest): Запрос на смену карты для автосписаний

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, PaymentCreateResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ChangePaymentMethodRequest,
) -> Optional[Union[HTTPValidationError, PaymentCreateResponse]]:
    r"""Change Payment Method

     Endpoint: Смена карты для автосписаний

    Создает платеж с минимальной суммой (по умолчанию 1 рубль) для привязки новой карты.
    После успешной оплаты новая карта будет использоваться для автосписаний.

    POST /api/v1/payments/change-payment-method
    {
        \"user_id\": 1,
        \"return_url\": \"https://yourdomain.com/payment/success\",
        \"amount\": 1.0
    }

    Response:
    {
        \"success\": true,
        \"message\": \"Платеж создан для привязки новой карты. После успешной оплаты карта будет
    обновлена.\",
        \"confirmation_url\": \"https://yookassa.ru/payments/...\",
        \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\"
    }

    Args:
        body (ChangePaymentMethodRequest): Запрос на смену карты для автосписаний

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, PaymentCreateResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
