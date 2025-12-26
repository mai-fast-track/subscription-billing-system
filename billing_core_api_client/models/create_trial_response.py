import datetime
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="CreateTrialResponse")


@_attrs_define
class CreateTrialResponse:
    """Схема ответа при создании промопериода

    Attributes:
        subscription_id (int): ID созданной подписки
        payment_id (int): ID созданного платежа
        end_date (datetime.datetime): Дата окончания промопериода
        message (str): Сообщение о результате
    """

    subscription_id: int
    payment_id: int
    end_date: datetime.datetime
    message: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subscription_id = self.subscription_id

        payment_id = self.payment_id

        end_date = self.end_date.isoformat()

        message = self.message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subscription_id": subscription_id,
                "payment_id": payment_id,
                "end_date": end_date,
                "message": message,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        subscription_id = d.pop("subscription_id")

        payment_id = d.pop("payment_id")

        end_date = isoparse(d.pop("end_date"))

        message = d.pop("message")

        create_trial_response = cls(
            subscription_id=subscription_id,
            payment_id=payment_id,
            end_date=end_date,
            message=message,
        )

        create_trial_response.additional_properties = d
        return create_trial_response

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
