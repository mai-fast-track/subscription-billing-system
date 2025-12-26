from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar(
    "T",
    bound="TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost",
)


@_attrs_define
class TestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPostResponseTestAutoPaymentForSubscriptionApiV1AutoPaymentsTestSubscriptionSubscriptionIdPost:
    """ """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: dict[str, Any]) -> T:
        d = src_dict.copy()
        test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post_response_test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post = cls()

        test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post_response_test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post.additional_properties = d
        return test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post_response_test_auto_payment_for_subscription_api_v1_auto_payments_test_subscription_subscription_id_post

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
