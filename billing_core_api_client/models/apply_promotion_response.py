import datetime
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="ApplyPromotionResponse")


@_attrs_define
class ApplyPromotionResponse:
    """Схема ответа при применении промокода к подписке

    Attributes:
        success (bool): Успешно ли применен промокод
        message (str): Сообщение о результате
        subscription_id (int): ID подписки
        old_end_date (datetime.datetime): Дата окончания до применения промокода
        new_end_date (datetime.datetime): Дата окончания после применения промокода
        bonus_days (int): Количество добавленных бонусных дней
    """

    success: bool
    message: str
    subscription_id: int
    old_end_date: datetime.datetime
    new_end_date: datetime.datetime
    bonus_days: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        message = self.message

        subscription_id = self.subscription_id

        old_end_date = self.old_end_date.isoformat()

        new_end_date = self.new_end_date.isoformat()

        bonus_days = self.bonus_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
                "message": message,
                "subscription_id": subscription_id,
                "old_end_date": old_end_date,
                "new_end_date": new_end_date,
                "bonus_days": bonus_days,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        success = d.pop("success")

        message = d.pop("message")

        subscription_id = d.pop("subscription_id")

        old_end_date = isoparse(d.pop("old_end_date"))

        new_end_date = isoparse(d.pop("new_end_date"))

        bonus_days = d.pop("bonus_days")

        apply_promotion_response = cls(
            success=success,
            message=message,
            subscription_id=subscription_id,
            old_end_date=old_end_date,
            new_end_date=new_end_date,
            bonus_days=bonus_days,
        )

        apply_promotion_response.additional_properties = d
        return apply_promotion_response

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
