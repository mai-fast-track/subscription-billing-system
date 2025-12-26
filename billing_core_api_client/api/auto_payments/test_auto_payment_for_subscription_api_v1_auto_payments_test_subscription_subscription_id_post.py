from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post_response_test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post import (
    TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost,
)
from ...types import Response


def _get_kwargs(
    subscription_id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/auto-payments/test-subscription/{subscription_id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        HTTPValidationError,
        TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost,
    ]
]:
    if response.status_code == 200:
        response_200 = TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost.from_dict(
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
        TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost,
    ]
]:
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
) -> Response[
    Union[
        HTTPValidationError,
        TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost,
    ]
]:
    """Test Auto Payment For Subscription

     Протестировать автоплатеж для конкретной подписки.
    Полезно для отладки.

    POST /api/v1/auto-payments/test-subscription/{subscription_id}

    Args:
        subscription_id: ID подписки для тестирования

    Returns:
        Dict с результатом тестирования

    Args:
        subscription_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost]]
    """

    kwargs = _get_kwargs(
        subscription_id=subscription_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    subscription_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[
        HTTPValidationError,
        TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost,
    ]
]:
    """Test Auto Payment For Subscription

     Протестировать автоплатеж для конкретной подписки.
    Полезно для отладки.

    POST /api/v1/auto-payments/test-subscription/{subscription_id}

    Args:
        subscription_id: ID подписки для тестирования

    Returns:
        Dict с результатом тестирования

    Args:
        subscription_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost]
    """

    return sync_detailed(
        subscription_id=subscription_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    subscription_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[
    Union[
        HTTPValidationError,
        TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost,
    ]
]:
    """Test Auto Payment For Subscription

     Протестировать автоплатеж для конкретной подписки.
    Полезно для отладки.

    POST /api/v1/auto-payments/test-subscription/{subscription_id}

    Args:
        subscription_id: ID подписки для тестирования

    Returns:
        Dict с результатом тестирования

    Args:
        subscription_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost]]
    """

    kwargs = _get_kwargs(
        subscription_id=subscription_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    subscription_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[
    Union[
        HTTPValidationError,
        TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost,
    ]
]:
    """Test Auto Payment For Subscription

     Протестировать автоплатеж для конкретной подписки.
    Полезно для отладки.

    POST /api/v1/auto-payments/test-subscription/{subscription_id}

    Args:
        subscription_id: ID подписки для тестирования

    Returns:
        Dict с результатом тестирования

    Args:
        subscription_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost]
    """

    return (
        await asyncio_detailed(
            subscription_id=subscription_id,
            client=client,
        )
    ).parsed
