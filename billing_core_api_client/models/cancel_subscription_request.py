from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CancelSubscriptionRequest")


@_attrs_define
class CancelSubscriptionRequest:
    """Схема запроса на отмену подписки

    Attributes:
        with_refund (Union[Unset, bool]): Выполнить возврат средств. Если True - подписка отменяется сразу с возвратом
            за неиспользованную часть. Если False - подписка активна до end_date без возврата (по умолчанию) Default: False.
    """

    with_refund: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        with_refund = self.with_refund

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if with_refund is not UNSET:
            field_dict["with_refund"] = with_refund

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        with_refund = d.pop("with_refund", UNSET)

        cancel_subscription_request = cls(
            with_refund=with_refund,
        )

        cancel_subscription_request.additional_properties = d
        return cancel_subscription_request

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
