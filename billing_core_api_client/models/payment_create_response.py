from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PaymentCreateResponse")


@_attrs_define
class PaymentCreateResponse:
    """Ответ: платеж создан, вот ссылка на оплату

    Attributes:
        success (bool): Успешно ли создан платеж
        message (str): Сообщение
        confirmation_url (str): URL для подтверждения оплаты
        yookassa_payment_id (str): ID платежа в Юкассе
    """

    success: bool
    message: str
    confirmation_url: str
    yookassa_payment_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        message = self.message

        confirmation_url = self.confirmation_url

        yookassa_payment_id = self.yookassa_payment_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
                "message": message,
                "confirmation_url": confirmation_url,
                "yookassa_payment_id": yookassa_payment_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        success = d.pop("success")

        message = d.pop("message")

        confirmation_url = d.pop("confirmation_url")

        yookassa_payment_id = d.pop("yookassa_payment_id")

        payment_create_response = cls(
            success=success,
            message=message,
            confirmation_url=confirmation_url,
            yookassa_payment_id=yookassa_payment_id,
        )

        payment_create_response.additional_properties = d
        return payment_create_response

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
