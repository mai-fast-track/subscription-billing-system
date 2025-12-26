from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.payment_with_subscription_response import PaymentWithSubscriptionResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    user_id: int,
    *,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/payments/user/{user_id}/completed",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, list["PaymentWithSubscriptionResponse"]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = PaymentWithSubscriptionResponse.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[Union[HTTPValidationError, list["PaymentWithSubscriptionResponse"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    user_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
) -> Response[Union[HTTPValidationError, list["PaymentWithSubscriptionResponse"]]]:
    r"""Get User Completed Payments

     Endpoint: Получить платежи пользователя в конечных статусах (succeeded, cancelled, failed)

    Возвращает только завершенные платежи (успешные, отмененные или неудачные).
    Не включает pending и waiting_for_capture платежи.

    GET /api/v1/payments/user/{user_id}/completed?skip=0&limit=100

    Response:
    [
        {
            \"id\": 1,
            \"user_id\": 1,
            \"subscription_id\": 5,
            \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\",
            \"amount\": 99.00,
            \"currency\": \"RUB\",
            \"status\": \"succeeded\",
            \"payment_method\": \"manual\",
            \"attempt_number\": 1,
            \"created_at\": \"2025-01-27T12:00:00Z\",
            \"updated_at\": \"2025-01-27T12:00:00Z\",
            \"subscription_plan_name\": \"Premium\",
            \"subscription_status\": \"active\"
        }
    ]

    Args:
        user_id (int):
        skip (Union[Unset, int]): Количество пропущенных записей Default: 0.
        limit (Union[Unset, int]): Максимальное количество записей Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['PaymentWithSubscriptionResponse']]]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        skip=skip,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    user_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
) -> Optional[Union[HTTPValidationError, list["PaymentWithSubscriptionResponse"]]]:
    r"""Get User Completed Payments

     Endpoint: Получить платежи пользователя в конечных статусах (succeeded, cancelled, failed)

    Возвращает только завершенные платежи (успешные, отмененные или неудачные).
    Не включает pending и waiting_for_capture платежи.

    GET /api/v1/payments/user/{user_id}/completed?skip=0&limit=100

    Response:
    [
        {
            \"id\": 1,
            \"user_id\": 1,
            \"subscription_id\": 5,
            \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\",
            \"amount\": 99.00,
            \"currency\": \"RUB\",
            \"status\": \"succeeded\",
            \"payment_method\": \"manual\",
            \"attempt_number\": 1,
            \"created_at\": \"2025-01-27T12:00:00Z\",
            \"updated_at\": \"2025-01-27T12:00:00Z\",
            \"subscription_plan_name\": \"Premium\",
            \"subscription_status\": \"active\"
        }
    ]

    Args:
        user_id (int):
        skip (Union[Unset, int]): Количество пропущенных записей Default: 0.
        limit (Union[Unset, int]): Максимальное количество записей Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['PaymentWithSubscriptionResponse']]
    """

    return sync_detailed(
        user_id=user_id,
        client=client,
        skip=skip,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    user_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
) -> Response[Union[HTTPValidationError, list["PaymentWithSubscriptionResponse"]]]:
    r"""Get User Completed Payments

     Endpoint: Получить платежи пользователя в конечных статусах (succeeded, cancelled, failed)

    Возвращает только завершенные платежи (успешные, отмененные или неудачные).
    Не включает pending и waiting_for_capture платежи.

    GET /api/v1/payments/user/{user_id}/completed?skip=0&limit=100

    Response:
    [
        {
            \"id\": 1,
            \"user_id\": 1,
            \"subscription_id\": 5,
            \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\",
            \"amount\": 99.00,
            \"currency\": \"RUB\",
            \"status\": \"succeeded\",
            \"payment_method\": \"manual\",
            \"attempt_number\": 1,
            \"created_at\": \"2025-01-27T12:00:00Z\",
            \"updated_at\": \"2025-01-27T12:00:00Z\",
            \"subscription_plan_name\": \"Premium\",
            \"subscription_status\": \"active\"
        }
    ]

    Args:
        user_id (int):
        skip (Union[Unset, int]): Количество пропущенных записей Default: 0.
        limit (Union[Unset, int]): Максимальное количество записей Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, list['PaymentWithSubscriptionResponse']]]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        skip=skip,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    user_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
) -> Optional[Union[HTTPValidationError, list["PaymentWithSubscriptionResponse"]]]:
    r"""Get User Completed Payments

     Endpoint: Получить платежи пользователя в конечных статусах (succeeded, cancelled, failed)

    Возвращает только завершенные платежи (успешные, отмененные или неудачные).
    Не включает pending и waiting_for_capture платежи.

    GET /api/v1/payments/user/{user_id}/completed?skip=0&limit=100

    Response:
    [
        {
            \"id\": 1,
            \"user_id\": 1,
            \"subscription_id\": 5,
            \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\",
            \"amount\": 99.00,
            \"currency\": \"RUB\",
            \"status\": \"succeeded\",
            \"payment_method\": \"manual\",
            \"attempt_number\": 1,
            \"created_at\": \"2025-01-27T12:00:00Z\",
            \"updated_at\": \"2025-01-27T12:00:00Z\",
            \"subscription_plan_name\": \"Premium\",
            \"subscription_status\": \"active\"
        }
    ]

    Args:
        user_id (int):
        skip (Union[Unset, int]): Количество пропущенных записей Default: 0.
        limit (Union[Unset, int]): Максимальное количество записей Default: 100.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, list['PaymentWithSubscriptionResponse']]
    """

    return (
        await asyncio_detailed(
            user_id=user_id,
            client=client,
            skip=skip,
            limit=limit,
        )
    ).parsed
