import datetime
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.payment_status import PaymentStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="PaymentWithSubscriptionResponse")


@_attrs_define
class PaymentWithSubscriptionResponse:
    """Платеж с информацией о подписке и возвратах

    Attributes:
        id (int): ID платежа
        user_id (int): ID пользователя
        subscription_id (int): ID подписки
        yookassa_payment_id (str): ID платежа в Юкассе
        amount (float): Сумма платежа
        status (PaymentStatus): Статусы платежей в системе
        created_at (datetime.datetime): Дата создания
        updated_at (datetime.datetime): Дата обновления
        currency (Union[Unset, str]): Валюта Default: 'RUB'.
        payment_method (Union[None, Unset, str]): Метод платежа
        attempt_number (Union[Unset, int]): Номер попытки Default: 1.
        subscription_plan_name (Union[None, Unset, str]): Название плана подписки
        subscription_status (Union[None, Unset, str]): Статус подписки
        refund_amount (Union[None, Unset, float]): Сумма возврата (если есть)
        refund_status (Union[None, Unset, str]): Статус возврата (pending, succeeded, failed, cancelled)
    """

    id: int
    user_id: int
    subscription_id: int
    yookassa_payment_id: str
    amount: float
    status: PaymentStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    currency: Union[Unset, str] = "RUB"
    payment_method: Union[None, Unset, str] = UNSET
    attempt_number: Union[Unset, int] = 1
    subscription_plan_name: Union[None, Unset, str] = UNSET
    subscription_status: Union[None, Unset, str] = UNSET
    refund_amount: Union[None, Unset, float] = UNSET
    refund_status: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        user_id = self.user_id

        subscription_id = self.subscription_id

        yookassa_payment_id = self.yookassa_payment_id

        amount = self.amount

        status = self.status.value

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        currency = self.currency

        payment_method: Union[None, Unset, str]
        if isinstance(self.payment_method, Unset):
            payment_method = UNSET
        else:
            payment_method = self.payment_method

        attempt_number = self.attempt_number

        subscription_plan_name: Union[None, Unset, str]
        if isinstance(self.subscription_plan_name, Unset):
            subscription_plan_name = UNSET
        else:
            subscription_plan_name = self.subscription_plan_name

        subscription_status: Union[None, Unset, str]
        if isinstance(self.subscription_status, Unset):
            subscription_status = UNSET
        else:
            subscription_status = self.subscription_status

        refund_amount: Union[None, Unset, float]
        if isinstance(self.refund_amount, Unset):
            refund_amount = UNSET
        else:
            refund_amount = self.refund_amount

        refund_status: Union[None, Unset, str]
        if isinstance(self.refund_status, Unset):
            refund_status = UNSET
        else:
            refund_status = self.refund_status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "user_id": user_id,
                "subscription_id": subscription_id,
                "yookassa_payment_id": yookassa_payment_id,
                "amount": amount,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if currency is not UNSET:
            field_dict["currency"] = currency
        if payment_method is not UNSET:
            field_dict["payment_method"] = payment_method
        if attempt_number is not UNSET:
            field_dict["attempt_number"] = attempt_number
        if subscription_plan_name is not UNSET:
            field_dict["subscription_plan_name"] = subscription_plan_name
        if subscription_status is not UNSET:
            field_dict["subscription_status"] = subscription_status
        if refund_amount is not UNSET:
            field_dict["refund_amount"] = refund_amount
        if refund_status is not UNSET:
            field_dict["refund_status"] = refund_status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        user_id = d.pop("user_id")

        subscription_id = d.pop("subscription_id")

        yookassa_payment_id = d.pop("yookassa_payment_id")

        amount = d.pop("amount")

        status = PaymentStatus(d.pop("status"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        currency = d.pop("currency", UNSET)

        def _parse_payment_method(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        payment_method = _parse_payment_method(d.pop("payment_method", UNSET))

        attempt_number = d.pop("attempt_number", UNSET)

        def _parse_subscription_plan_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        subscription_plan_name = _parse_subscription_plan_name(d.pop("subscription_plan_name", UNSET))

        def _parse_subscription_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        subscription_status = _parse_subscription_status(d.pop("subscription_status", UNSET))

        def _parse_refund_amount(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        refund_amount = _parse_refund_amount(d.pop("refund_amount", UNSET))

        def _parse_refund_status(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        refund_status = _parse_refund_status(d.pop("refund_status", UNSET))

        payment_with_subscription_response = cls(
            id=id,
            user_id=user_id,
            subscription_id=subscription_id,
            yookassa_payment_id=yookassa_payment_id,
            amount=amount,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            currency=currency,
            payment_method=payment_method,
            attempt_number=attempt_number,
            subscription_plan_name=subscription_plan_name,
            subscription_status=subscription_status,
            refund_amount=refund_amount,
            refund_status=refund_status,
        )

        payment_with_subscription_response.additional_properties = d
        return payment_with_subscription_response

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
