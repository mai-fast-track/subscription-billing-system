from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SubscriptionPlanCreateRequest")


@_attrs_define
class SubscriptionPlanCreateRequest:
    """Схема для создания плана подписки

    Attributes:
        name (str): Название плана
        price (float): Цена плана
        duration_days (int): Длительность в днях
        features (Union[None, Unset, str]): Описание возможностей
    """

    name: str
    price: float
    duration_days: int
    features: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        price = self.price

        duration_days = self.duration_days

        features: Union[None, Unset, str]
        if isinstance(self.features, Unset):
            features = UNSET
        else:
            features = self.features

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "price": price,
                "duration_days": duration_days,
            }
        )
        if features is not UNSET:
            field_dict["features"] = features

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name")

        price = d.pop("price")

        duration_days = d.pop("duration_days")

        def _parse_features(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        features = _parse_features(d.pop("features", UNSET))

        subscription_plan_create_request = cls(
            name=name,
            price=price,
            duration_days=duration_days,
            features=features,
        )

        subscription_plan_create_request.additional_properties = d
        return subscription_plan_create_request

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
