import datetime
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """Схема пользователя для ответа

    Attributes:
        telegram_id (int): Telegram ID пользователя
        id (int): ID пользователя
        role (str): Роль пользователя
        created_at (datetime.datetime): Дата создания
        updated_at (datetime.datetime): Дата обновления
    """

    telegram_id: int
    id: int
    role: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        telegram_id = self.telegram_id

        id = self.id

        role = self.role

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "telegram_id": telegram_id,
                "id": id,
                "role": role,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        telegram_id = d.pop("telegram_id")

        id = d.pop("id")

        role = d.pop("role")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        user = cls(
            telegram_id=telegram_id,
            id=id,
            role=role,
            created_at=created_at,
            updated_at=updated_at,
        )

        user.additional_properties = d
        return user

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
