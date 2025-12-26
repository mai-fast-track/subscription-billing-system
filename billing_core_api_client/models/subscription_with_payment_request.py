from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SubscriptionWithPaymentRequest")


@_attrs_define
class SubscriptionWithPaymentRequest:
    """Схема для создания подписки с платежом (обычное оформление без промопериода)

    Attributes:
        user_id (int): ID пользователя
        plan_id (int): ID плана подписки
        return_url (str): URL для возврата после оплаты
    """

    user_id: int
    plan_id: int
    return_url: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        plan_id = self.plan_id

        return_url = self.return_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "plan_id": plan_id,
                "return_url": return_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id")

        plan_id = d.pop("plan_id")

        return_url = d.pop("return_url")

        subscription_with_payment_request = cls(
            user_id=user_id,
            plan_id=plan_id,
            return_url=return_url,
        )

        subscription_with_payment_request.additional_properties = d
        return subscription_with_payment_request

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
