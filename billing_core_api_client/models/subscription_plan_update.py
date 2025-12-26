from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SubscriptionPlanUpdate")


@_attrs_define
class SubscriptionPlanUpdate:
    """Схема для обновления плана подписки

    Attributes:
        name (Union[None, Unset, str]): Название плана
        price (Union[None, Unset, float]): Цена плана
        duration_days (Union[None, Unset, int]): Длительность в днях
        features (Union[None, Unset, str]): Описание возможностей
    """

    name: Union[None, Unset, str] = UNSET
    price: Union[None, Unset, float] = UNSET
    duration_days: Union[None, Unset, int] = UNSET
    features: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        price: Union[None, Unset, float]
        if isinstance(self.price, Unset):
            price = UNSET
        else:
            price = self.price

        duration_days: Union[None, Unset, int]
        if isinstance(self.duration_days, Unset):
            duration_days = UNSET
        else:
            duration_days = self.duration_days

        features: Union[None, Unset, str]
        if isinstance(self.features, Unset):
            features = UNSET
        else:
            features = self.features

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if price is not UNSET:
            field_dict["price"] = price
        if duration_days is not UNSET:
            field_dict["duration_days"] = duration_days
        if features is not UNSET:
            field_dict["features"] = features

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_price(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        price = _parse_price(d.pop("price", UNSET))

        def _parse_duration_days(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        duration_days = _parse_duration_days(d.pop("duration_days", UNSET))

        def _parse_features(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        features = _parse_features(d.pop("features", UNSET))

        subscription_plan_update = cls(
            name=name,
            price=price,
            duration_days=duration_days,
            features=features,
        )

        subscription_plan_update.additional_properties = d
        return subscription_plan_update

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
