from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.retry_auto_payment_api_v1_auto_payments_retry_payment_payment_id_attempt_post_response_retry_auto_payment_api_v1_auto_payments_retry_payment_payment_id_attempt_post import (
    RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost,
)
from ...types import Response


def _get_kwargs(
    payment_id: int,
    attempt: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/auto-payments/retry-payment/{payment_id}/{attempt}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        HTTPValidationError,
        RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost,
    ]
]:
    if response.status_code == 200:
        response_200 = RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost.from_dict(
            response.json()
        )

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
) -> Response[
    Union[
        HTTPValidationError,
        RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    payment_id: int,
    attempt: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    Union[
        HTTPValidationError,
        RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost,
    ]
]:
    """Retry Auto Payment

     Ручной запуск попытки автосписания (новая архитектура).
    Запускает Celery задачу retry_auto_payment_attempt.

    POST /api/v1/auto-payments/retry-payment/{payment_id}/{attempt}

    Args:
        payment_id: ID платежа
        attempt: Номер попытки (начинается с 1)

    Returns:
        Dict с task_id

    Args:
        payment_id (int):
        attempt (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost]]
    """

    kwargs = _get_kwargs(
        payment_id=payment_id,
        attempt=attempt,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    payment_id: int,
    attempt: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[
        HTTPValidationError,
        RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost,
    ]
]:
    """Retry Auto Payment

     Ручной запуск попытки автосписания (новая архитектура).
    Запускает Celery задачу retry_auto_payment_attempt.

    POST /api/v1/auto-payments/retry-payment/{payment_id}/{attempt}

    Args:
        payment_id: ID платежа
        attempt: Номер попытки (начинается с 1)

    Returns:
        Dict с task_id

    Args:
        payment_id (int):
        attempt (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost]
    """

    return sync_detailed(
        payment_id=payment_id,
        attempt=attempt,
        client=client,
    ).parsed


async def asyncio_detailed(
    payment_id: int,
    attempt: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    Union[
        HTTPValidationError,
        RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost,
    ]
]:
    """Retry Auto Payment

     Ручной запуск попытки автосписания (новая архитектура).
    Запускает Celery задачу retry_auto_payment_attempt.

    POST /api/v1/auto-payments/retry-payment/{payment_id}/{attempt}

    Args:
        payment_id: ID платежа
        attempt: Номер попытки (начинается с 1)

    Returns:
        Dict с task_id

    Args:
        payment_id (int):
        attempt (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost]]
    """

    kwargs = _get_kwargs(
        payment_id=payment_id,
        attempt=attempt,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    payment_id: int,
    attempt: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[
        HTTPValidationError,
        RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost,
    ]
]:
    """Retry Auto Payment

     Ручной запуск попытки автосписания (новая архитектура).
    Запускает Celery задачу retry_auto_payment_attempt.

    POST /api/v1/auto-payments/retry-payment/{payment_id}/{attempt}

    Args:
        payment_id: ID платежа
        attempt: Номер попытки (начинается с 1)

    Returns:
        Dict с task_id

    Args:
        payment_id (int):
        attempt (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, RetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPostResponseRetryAutoPaymentApiV1AutoPaymentsRetryPaymentPaymentIdAttemptPost]
    """

    return (
        await asyncio_detailed(
            payment_id=payment_id,
            attempt=attempt,
            client=client,
        )
    ).parsed
