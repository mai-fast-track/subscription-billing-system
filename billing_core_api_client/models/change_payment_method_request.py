from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ChangePaymentMethodRequest")


@_attrs_define
class ChangePaymentMethodRequest:
    """Запрос на смену карты для автосписаний

    Attributes:
        user_id (int): ID пользователя
        return_url (str): URL для возврата после оплаты
        amount (Union[Unset, float]): Минимальная сумма для привязки карты (по умолчанию 1 рубль) Default: 1.0.
    """

    user_id: int
    return_url: str
    amount: Union[Unset, float] = 1.0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        return_url = self.return_url

        amount = self.amount

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "return_url": return_url,
            }
        )
        if amount is not UNSET:
            field_dict["amount"] = amount

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id")

        return_url = d.pop("return_url")

        amount = d.pop("amount", UNSET)

        change_payment_method_request = cls(
            user_id=user_id,
            return_url=return_url,
            amount=amount,
        )

        change_payment_method_request.additional_properties = d
        return change_payment_method_request

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
