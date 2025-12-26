from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.promotion import Promotion
from ...models.promotion_update import PromotionUpdate
from ...types import Response


def _get_kwargs(
    promotion_id: int,
    *,
    body: PromotionUpdate,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/api/v1/promotions/{promotion_id}",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, Promotion]]:
    if response.status_code == 200:
        response_200 = Promotion.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, Promotion]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    promotion_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: PromotionUpdate,
) -> Response[Union[HTTPValidationError, Promotion]]:
    """Update Promotion

     Обновить промокод

    Args:
        promotion_id (int):
        body (PromotionUpdate): Схема для обновления промокода

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Promotion]]
    """

    kwargs = _get_kwargs(
        promotion_id=promotion_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    promotion_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: PromotionUpdate,
) -> Optional[Union[HTTPValidationError, Promotion]]:
    """Update Promotion

     Обновить промокод

    Args:
        promotion_id (int):
        body (PromotionUpdate): Схема для обновления промокода

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Promotion]
    """

    return sync_detailed(
        promotion_id=promotion_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    promotion_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: PromotionUpdate,
) -> Response[Union[HTTPValidationError, Promotion]]:
    """Update Promotion

     Обновить промокод

    Args:
        promotion_id (int):
        body (PromotionUpdate): Схема для обновления промокода

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Promotion]]
    """

    kwargs = _get_kwargs(
        promotion_id=promotion_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    promotion_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: PromotionUpdate,
) -> Optional[Union[HTTPValidationError, Promotion]]:
    """Update Promotion

     Обновить промокод

    Args:
        promotion_id (int):
        body (PromotionUpdate): Схема для обновления промокода

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Promotion]
    """

    return (
        await asyncio_detailed(
            promotion_id=promotion_id,
            client=client,
            body=body,
        )
    ).parsed
