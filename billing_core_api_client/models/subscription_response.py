import datetime
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.subscription_status import SubscriptionStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="SubscriptionResponse")


@_attrs_define
class SubscriptionResponse:
    """Схема подписки для ответа

    Attributes:
        plan_id (int): ID плана подписки
        start_date (datetime.datetime): Дата начала подписки
        end_date (datetime.datetime): Дата окончания подписки
        id (int): ID подписки
        user_id (int): ID пользователя
        created_at (datetime.datetime): Дата создания
        updated_at (datetime.datetime): Дата обновления
        status (Union[Unset, SubscriptionStatus]):  Default: SubscriptionStatus.ACTIVE.
    """

    plan_id: int
    start_date: datetime.datetime
    end_date: datetime.datetime
    id: int
    user_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: Union[Unset, SubscriptionStatus] = SubscriptionStatus.ACTIVE
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        plan_id = self.plan_id

        start_date = self.start_date.isoformat()

        end_date = self.end_date.isoformat()

        id = self.id

        user_id = self.user_id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "plan_id": plan_id,
                "start_date": start_date,
                "end_date": end_date,
                "id": id,
                "user_id": user_id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        plan_id = d.pop("plan_id")

        start_date = isoparse(d.pop("start_date"))

        end_date = isoparse(d.pop("end_date"))

        id = d.pop("id")

        user_id = d.pop("user_id")

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        _status = d.pop("status", UNSET)
        status: Union[Unset, SubscriptionStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = SubscriptionStatus(_status)

        subscription_response = cls(
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            id=id,
            user_id=user_id,
            created_at=created_at,
            updated_at=updated_at,
            status=status,
        )

        subscription_response.additional_properties = d
        return subscription_response

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
