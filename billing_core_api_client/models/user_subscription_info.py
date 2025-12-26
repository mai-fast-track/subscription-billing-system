from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.subscription_detail_response import SubscriptionDetailResponse
    from ..models.subscription_response import SubscriptionResponse


T = TypeVar("T", bound="UserSubscriptionInfo")


@_attrs_define
class UserSubscriptionInfo:
    """Информация о подписках пользователя

    Attributes:
        active_subscription (Union['SubscriptionDetailResponse', None, Unset]): Активная подписка
        subscription_history (Union[Unset, list['SubscriptionResponse']]): История подписок
    """

    active_subscription: Union["SubscriptionDetailResponse", None, Unset] = UNSET
    subscription_history: Union[Unset, list["SubscriptionResponse"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.subscription_detail_response import SubscriptionDetailResponse

        active_subscription: Union[None, Unset, dict[str, Any]]
        if isinstance(self.active_subscription, Unset):
            active_subscription = UNSET
        elif isinstance(self.active_subscription, SubscriptionDetailResponse):
            active_subscription = self.active_subscription.to_dict()
        else:
            active_subscription = self.active_subscription

        subscription_history: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.subscription_history, Unset):
            subscription_history = []
            for subscription_history_item_data in self.subscription_history:
                subscription_history_item = subscription_history_item_data.to_dict()
                subscription_history.append(subscription_history_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if active_subscription is not UNSET:
            field_dict["active_subscription"] = active_subscription
        if subscription_history is not UNSET:
            field_dict["subscription_history"] = subscription_history

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        from ..models.subscription_detail_response import SubscriptionDetailResponse
        from ..models.subscription_response import SubscriptionResponse

        d = src_dict.copy()

        def _parse_active_subscription(data: object) -> Union["SubscriptionDetailResponse", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                active_subscription_type_0 = SubscriptionDetailResponse.from_dict(data)

                return active_subscription_type_0
            except:  # noqa: E722
                pass
            return cast(Union["SubscriptionDetailResponse", None, Unset], data)

        active_subscription = _parse_active_subscription(d.pop("active_subscription", UNSET))

        subscription_history = []
        _subscription_history = d.pop("subscription_history", UNSET)
        for subscription_history_item_data in _subscription_history or []:
            subscription_history_item = SubscriptionResponse.from_dict(subscription_history_item_data)

            subscription_history.append(subscription_history_item)

        user_subscription_info = cls(
            active_subscription=active_subscription,
            subscription_history=subscription_history,
        )

        user_subscription_info.additional_properties = d
        return user_subscription_info

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
