import datetime
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.subscription_status import SubscriptionStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="SubscriptionCreateRequestSchema")


@_attrs_define
class SubscriptionCreateRequestSchema:
    """Схема для создания подписки

    Attributes:
        user_id (int): ID пользователя
        plan_id (int): ID плана подписки
        start_date (Union[None, Unset, datetime.datetime]): Дата начала подписки
        status (Union[None, SubscriptionStatus, Unset]): Статус подписки
    """

    user_id: int
    plan_id: int
    start_date: Union[None, Unset, datetime.datetime] = UNSET
    status: Union[None, SubscriptionStatus, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        plan_id = self.plan_id

        start_date: Union[None, Unset, str]
        if isinstance(self.start_date, Unset):
            start_date = UNSET
        elif isinstance(self.start_date, datetime.datetime):
            start_date = self.start_date.isoformat()
        else:
            start_date = self.start_date

        status: Union[None, Unset, str]
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, SubscriptionStatus):
            status = self.status.value
        else:
            status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "plan_id": plan_id,
            }
        )
        if start_date is not UNSET:
            field_dict["start_date"] = start_date
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        user_id = d.pop("user_id")

        plan_id = d.pop("plan_id")

        def _parse_start_date(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_date_type_0 = isoparse(data)

                return start_date_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        start_date = _parse_start_date(d.pop("start_date", UNSET))

        def _parse_status(data: object) -> Union[None, SubscriptionStatus, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = SubscriptionStatus(data)

                return status_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, SubscriptionStatus, Unset], data)

        status = _parse_status(d.pop("status", UNSET))

        subscription_create_request_schema = cls(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            status=status,
        )

        subscription_create_request_schema.additional_properties = d
        return subscription_create_request_schema

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
