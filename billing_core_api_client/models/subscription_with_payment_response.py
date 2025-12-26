from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SubscriptionWithPaymentResponse")


@_attrs_define
class SubscriptionWithPaymentResponse:
    """Схема ответа при создании подписки с платежом

    Attributes:
        subscription_id (int): ID созданной подписки
        payment_id (int): ID созданного платежа
        message (str): Сообщение о результате
        confirmation_url (Union[None, Unset, str]): URL для подтверждения оплаты (None для промопериода)
        yookassa_payment_id (Union[None, Unset, str]): ID платежа в Юкассе (None для промопериода)
        is_trial (Union[Unset, bool]): Флаг промопериода Default: False.
    """

    subscription_id: int
    payment_id: int
    message: str
    confirmation_url: Union[None, Unset, str] = UNSET
    yookassa_payment_id: Union[None, Unset, str] = UNSET
    is_trial: Union[Unset, bool] = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subscription_id = self.subscription_id

        payment_id = self.payment_id

        message = self.message

        confirmation_url: Union[None, Unset, str]
        if isinstance(self.confirmation_url, Unset):
            confirmation_url = UNSET
        else:
            confirmation_url = self.confirmation_url

        yookassa_payment_id: Union[None, Unset, str]
        if isinstance(self.yookassa_payment_id, Unset):
            yookassa_payment_id = UNSET
        else:
            yookassa_payment_id = self.yookassa_payment_id

        is_trial = self.is_trial

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subscription_id": subscription_id,
                "payment_id": payment_id,
                "message": message,
            }
        )
        if confirmation_url is not UNSET:
            field_dict["confirmation_url"] = confirmation_url
        if yookassa_payment_id is not UNSET:
            field_dict["yookassa_payment_id"] = yookassa_payment_id
        if is_trial is not UNSET:
            field_dict["is_trial"] = is_trial

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        subscription_id = d.pop("subscription_id")

        payment_id = d.pop("payment_id")

        message = d.pop("message")

        def _parse_confirmation_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        confirmation_url = _parse_confirmation_url(d.pop("confirmation_url", UNSET))

        def _parse_yookassa_payment_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        yookassa_payment_id = _parse_yookassa_payment_id(d.pop("yookassa_payment_id", UNSET))

        is_trial = d.pop("is_trial", UNSET)

        subscription_with_payment_response = cls(
            subscription_id=subscription_id,
            payment_id=payment_id,
            message=message,
            confirmation_url=confirmation_url,
            yookassa_payment_id=yookassa_payment_id,
            is_trial=is_trial,
        )

        subscription_with_payment_response.additional_properties = d
        return subscription_with_payment_response

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
