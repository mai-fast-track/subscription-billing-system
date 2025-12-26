from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar(
    "T",
    bound="ProcessSingleSubscriptionApiV1AutoPaymentsProcessSubscriptionSubscriptionIdPostResponseProcessSingleSubscriptionApiV1AutoPaymentsProcessSubscriptionSubscriptionIdPost",
)


@_attrs_define
class ProcessSingleSubscriptionApiV1AutoPaymentsProcessSubscriptionSubscriptionIdPostResponseProcessSingleSubscriptionApiV1AutoPaymentsProcessSubscriptionSubscriptionIdPost:
    """ """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post_response_process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post = cls()

        process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post_response_process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post.additional_properties = d
        return process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post_response_process_single_subscription_api_v1_auto_payments_process_subscription_subscription_id_post

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
