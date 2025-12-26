from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.user import User
from ...types import UNSET, Response


def _get_kwargs(
    user_id: int,
    *,
    new_telegram_id: int,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["new_telegram_id"] = new_telegram_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/users/transfer/{user_id}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, User]]:
    if response.status_code == 200:
        response_200 = User.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, User]]:
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
    new_telegram_id: int,
) -> Response[Union[HTTPValidationError, User]]:
    """Transfer User

     Передать пользователя другому telegram_id

    Args:
        user_id (int):
        new_telegram_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, User]]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        new_telegram_id=new_telegram_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    user_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    new_telegram_id: int,
) -> Optional[Union[HTTPValidationError, User]]:
    """Transfer User

     Передать пользователя другому telegram_id

    Args:
        user_id (int):
        new_telegram_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, User]
    """

    return sync_detailed(
        user_id=user_id,
        client=client,
        new_telegram_id=new_telegram_id,
    ).parsed


async def asyncio_detailed(
    user_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    new_telegram_id: int,
) -> Response[Union[HTTPValidationError, User]]:
    """Transfer User

     Передать пользователя другому telegram_id

    Args:
        user_id (int):
        new_telegram_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, User]]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        new_telegram_id=new_telegram_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    user_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    new_telegram_id: int,
) -> Optional[Union[HTTPValidationError, User]]:
    """Transfer User

     Передать пользователя другому telegram_id

    Args:
        user_id (int):
        new_telegram_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, User]
    """

    return (
        await asyncio_detailed(
            user_id=user_id,
            client=client,
            new_telegram_id=new_telegram_id,
        )
    ).parsed
