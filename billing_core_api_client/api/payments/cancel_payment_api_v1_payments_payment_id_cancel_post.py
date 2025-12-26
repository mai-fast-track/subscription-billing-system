from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    payment_id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/payments/{payment_id}/cancel",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Union[Any, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    payment_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Any, HTTPValidationError]]:
    r"""Cancel Payment

     Endpoint: Отменить платеж

    Отменяет авторизованные средства для двухстадийного платежа.
    Можно использовать для отмены платежа до его проведения.

    POST /api/v1/payments/{payment_id}/cancel

    Response:
    {
        \"success\": true,
        \"message\": \"Платеж успешно отменен\",
        \"payment_id\": 1,
        \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\"
    }

    Args:
        payment_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        payment_id=payment_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    payment_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Any, HTTPValidationError]]:
    r"""Cancel Payment

     Endpoint: Отменить платеж

    Отменяет авторизованные средства для двухстадийного платежа.
    Можно использовать для отмены платежа до его проведения.

    POST /api/v1/payments/{payment_id}/cancel

    Response:
    {
        \"success\": true,
        \"message\": \"Платеж успешно отменен\",
        \"payment_id\": 1,
        \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\"
    }

    Args:
        payment_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        payment_id=payment_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    payment_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[Any, HTTPValidationError]]:
    r"""Cancel Payment

     Endpoint: Отменить платеж

    Отменяет авторизованные средства для двухстадийного платежа.
    Можно использовать для отмены платежа до его проведения.

    POST /api/v1/payments/{payment_id}/cancel

    Response:
    {
        \"success\": true,
        \"message\": \"Платеж успешно отменен\",
        \"payment_id\": 1,
        \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\"
    }

    Args:
        payment_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        payment_id=payment_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    payment_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[Any, HTTPValidationError]]:
    r"""Cancel Payment

     Endpoint: Отменить платеж

    Отменяет авторизованные средства для двухстадийного платежа.
    Можно использовать для отмены платежа до его проведения.

    POST /api/v1/payments/{payment_id}/cancel

    Response:
    {
        \"success\": true,
        \"message\": \"Платеж успешно отменен\",
        \"payment_id\": 1,
        \"yookassa_payment_id\": \"29f87ba5-000f-50df-a9f3-7a84e1cc9f45\"
    }

    Args:
        payment_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            payment_id=payment_id,
            client=client,
        )
    ).parsed
