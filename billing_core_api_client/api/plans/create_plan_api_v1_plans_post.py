from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.subscription_plan_create_request import SubscriptionPlanCreateRequest
from ...models.subscription_plan_response import SubscriptionPlanResponse
from ...types import Response


def _get_kwargs(
    *,
    body: SubscriptionPlanCreateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/plans/",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, SubscriptionPlanResponse]]:
    if response.status_code == 200:
        response_200 = SubscriptionPlanResponse.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, SubscriptionPlanResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SubscriptionPlanCreateRequest,
) -> Response[Union[HTTPValidationError, SubscriptionPlanResponse]]:
    """Create Plan

     Создать новый план подписки

    Args:
        body (SubscriptionPlanCreateRequest): Схема для создания плана подписки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, SubscriptionPlanResponse]]
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
    body: SubscriptionPlanCreateRequest,
) -> Optional[Union[HTTPValidationError, SubscriptionPlanResponse]]:
    """Create Plan

     Создать новый план подписки

    Args:
        body (SubscriptionPlanCreateRequest): Схема для создания плана подписки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, SubscriptionPlanResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SubscriptionPlanCreateRequest,
) -> Response[Union[HTTPValidationError, SubscriptionPlanResponse]]:
    """Create Plan

     Создать новый план подписки

    Args:
        body (SubscriptionPlanCreateRequest): Схема для создания плана подписки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, SubscriptionPlanResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: SubscriptionPlanCreateRequest,
) -> Optional[Union[HTTPValidationError, SubscriptionPlanResponse]]:
    """Create Plan

     Создать новый план подписки

    Args:
        body (SubscriptionPlanCreateRequest): Схема для создания плана подписки

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, SubscriptionPlanResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
