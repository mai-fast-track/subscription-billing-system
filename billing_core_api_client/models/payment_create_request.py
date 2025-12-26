from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PaymentCreateRequest")


@_attrs_define
class PaymentCreateRequest:
    """Запрос на создание платежа

    Attributes:
        user_id (int): ID пользователя
        subscription_id (int): ID подписки
        amount (float): Сумма платежа
        return_url (str): URL для возврата после оплаты
    """

    user_id: int
    subscription_id: int
    amount: float
    return_url: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        subscription_id = self.subscription_id

        amount = self.amount

        return_url = self.return_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "amount": amount,
                "return_url": return_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id")

        subscription_id = d.pop("subscription_id")

        amount = d.pop("amount")

        return_url = d.pop("return_url")

        payment_create_request = cls(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            return_url=return_url,
        )

        payment_create_request.additional_properties = d
        return payment_create_request

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
