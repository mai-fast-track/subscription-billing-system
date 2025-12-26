import datetime
from typing import Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Promotion")


@_attrs_define
class Promotion:
    """Схема промокода для ответа

    Attributes:
        code (str): Код промокода
        name (str): Название промокода
        type_ (Literal['bonus_days']):
        value (int): Количество бонусных дней
        valid_from (datetime.datetime): Дата начала действия
        id (int): ID промокода
        is_active (bool): Активен ли промокод
        current_uses (int): Текущее количество использований
        created_at (datetime.datetime): Дата создания
        updated_at (datetime.datetime): Дата обновления
        description (Union[None, Unset, str]): Описание
        valid_until (Union[None, Unset, datetime.datetime]): Дата окончания действия
        max_uses (Union[None, Unset, int]): Максимальное количество использований
        applicable_plans (Union[None, Unset, list[str]]): Список применимых планов
        assigned_user_id (Union[None, Unset, int]): ID пользователя, которому назначен промокод
    """

    code: str
    name: str
    type_: Literal["bonus_days"]
    value: int
    valid_from: datetime.datetime
    id: int
    is_active: bool
    current_uses: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: Union[None, Unset, str] = UNSET
    valid_until: Union[None, Unset, datetime.datetime] = UNSET
    max_uses: Union[None, Unset, int] = UNSET
    applicable_plans: Union[None, Unset, list[str]] = UNSET
    assigned_user_id: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        name = self.name

        type_ = self.type_

        value = self.value

        valid_from = self.valid_from.isoformat()

        id = self.id

        is_active = self.is_active

        current_uses = self.current_uses

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        valid_until: Union[None, Unset, str]
        if isinstance(self.valid_until, Unset):
            valid_until = UNSET
        elif isinstance(self.valid_until, datetime.datetime):
            valid_until = self.valid_until.isoformat()
        else:
            valid_until = self.valid_until

        max_uses: Union[None, Unset, int]
        if isinstance(self.max_uses, Unset):
            max_uses = UNSET
        else:
            max_uses = self.max_uses

        applicable_plans: Union[None, Unset, list[str]]
        if isinstance(self.applicable_plans, Unset):
            applicable_plans = UNSET
        elif isinstance(self.applicable_plans, list):
            applicable_plans = self.applicable_plans

        else:
            applicable_plans = self.applicable_plans

        assigned_user_id: Union[None, Unset, int]
        if isinstance(self.assigned_user_id, Unset):
            assigned_user_id = UNSET
        else:
            assigned_user_id = self.assigned_user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "name": name,
                "type": type_,
                "value": value,
                "valid_from": valid_from,
                "id": id,
                "is_active": is_active,
                "current_uses": current_uses,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if valid_until is not UNSET:
            field_dict["valid_until"] = valid_until
        if max_uses is not UNSET:
            field_dict["max_uses"] = max_uses
        if applicable_plans is not UNSET:
            field_dict["applicable_plans"] = applicable_plans
        if assigned_user_id is not UNSET:
            field_dict["assigned_user_id"] = assigned_user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        code = d.pop("code")

        name = d.pop("name")

        type_ = cast(Literal["bonus_days"], d.pop("type"))
        if type_ != "bonus_days":
            raise ValueError(f"type must match const 'bonus_days', got '{type_}'")

        value = d.pop("value")

        valid_from = isoparse(d.pop("valid_from"))

        id = d.pop("id")

        is_active = d.pop("is_active")

        current_uses = d.pop("current_uses")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_valid_until(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                valid_until_type_0 = isoparse(data)

                return valid_until_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        valid_until = _parse_valid_until(d.pop("valid_until", UNSET))

        def _parse_max_uses(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_uses = _parse_max_uses(d.pop("max_uses", UNSET))

        def _parse_applicable_plans(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                applicable_plans_type_0 = cast(list[str], data)

                return applicable_plans_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        applicable_plans = _parse_applicable_plans(d.pop("applicable_plans", UNSET))

        def _parse_assigned_user_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        assigned_user_id = _parse_assigned_user_id(d.pop("assigned_user_id", UNSET))

        promotion = cls(
            code=code,
            name=name,
            type_=type_,
            value=value,
            valid_from=valid_from,
            id=id,
            is_active=is_active,
            current_uses=current_uses,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            valid_until=valid_until,
            max_uses=max_uses,
            applicable_plans=applicable_plans,
            assigned_user_id=assigned_user_id,
        )

        promotion.additional_properties = d
        return promotion

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
