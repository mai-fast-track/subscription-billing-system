"""
Subscription service for bot
"""

import logging
import sys
from pathlib import Path
from typing import Optional

api_client_path = Path(__file__).parent.parent / "api-client"
if str(api_client_path) not in sys.path:
    sys.path.insert(0, str(api_client_path))

from billing_core_api_client.api.plans import (
    get_subscription_plan_api_v1_plans_plan_id_get,
    get_subscription_plans_api_v1_plans_get,
)
from billing_core_api_client.api.subscriptions import (
    apply_promotion_to_subscription_api_v1_subscriptions_subscription_id_apply_promotion_post,
    cancel_subscription_api_v1_subscriptions_subscription_id_cancel_patch,
    check_trial_eligibility_api_v1_subscriptions_check_trial_eligibility_user_id_get,
    create_subscription_with_payment_api_v1_subscriptions_create_with_payment_post,
    create_trial_subscription_api_v1_subscriptions_create_trial_post,
    get_subscription_api_v1_subscriptions_subscription_id_get,
    get_user_active_subscription_api_v1_subscriptions_user_user_id_active_get,
)
from billing_core_api_client.models import (
    ApplyPromotionRequest,
    ApplyPromotionResponse,
    CreateTrialRequest,
    CreateTrialResponse,
    HTTPValidationError,
    SubscriptionDetailResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
    SubscriptionWithPaymentRequest,
    SubscriptionWithPaymentResponse,
    TrialEligibilityResponse,
)
from bot.core.api_client import get_api_client, get_authenticated_client

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription operations"""

    async def get_all_plans(self, skip: int = 0, limit: int = 100) -> list[SubscriptionPlanResponse]:
        """
        Get all subscription plans

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of subscription plans

        Raises:
            Exception: If operation fails
        """
        client = get_api_client()
        try:
            async with client:
                response = await get_subscription_plans_api_v1_plans_get.asyncio(client=client, skip=skip, limit=limit)

                # Check for validation errors
                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error getting plans: {response}")
                    raise Exception(f"Validation error: {response}")

                # Happy path: return list of plans
                if isinstance(response, list):
                    return response

                logger.warning(f"Unexpected response type when getting plans: {type(response)}")
                return []
        except Exception as e:
            logger.error(f"Failed to get plans: {e}")
            raise

    async def get_plan_by_id(self, plan_id: int) -> Optional[SubscriptionPlanResponse]:
        """
        Get subscription plan by ID

        Args:
            plan_id: Plan ID

        Returns:
            SubscriptionPlanResponse or None if not found

        Raises:
            Exception: If operation fails
        """
        client = get_api_client()
        try:
            async with client:
                response = await get_subscription_plan_api_v1_plans_plan_id_get.asyncio(plan_id=plan_id, client=client)


                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error getting plan {plan_id}: {response}")
                    return None

                if isinstance(response, SubscriptionPlanResponse):
                    return response

                logger.warning(f"Unexpected response type when getting plan {plan_id}: {type(response)}")
                return None
        except Exception as e:
            logger.error(f"Failed to get plan: {e}")
            return None

    async def get_active_subscription(self, user_id: int, token: str) -> Optional[SubscriptionDetailResponse]:
        """
        Get active subscription for user

        Args:
            user_id: User ID
            token: Authentication token

        Returns:
            SubscriptionDetailResponse or None if no active subscription

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                response = await get_user_active_subscription_api_v1_subscriptions_user_user_id_active_get.asyncio(
                    user_id=user_id, client=auth_client
                )


                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error getting active subscription for user {user_id}: {response}")
                    return None


                if isinstance(response, SubscriptionDetailResponse):
                    return response


                if response is None:
                    return None


                logger.warning(f"Unexpected response type when getting active subscription: {type(response)}")
                return None
        except Exception as e:
            logger.error(f"Failed to get active subscription: {e}")
            return None

    async def get_subscription_by_id(self, subscription_id: int, token: str) -> Optional[SubscriptionDetailResponse]:
        """
        Get subscription by ID

        Args:
            subscription_id: Subscription ID
            token: Authentication token

        Returns:
            SubscriptionDetailResponse or None if not found

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                response = await get_subscription_api_v1_subscriptions_subscription_id_get.asyncio(
                    subscription_id=subscription_id, client=auth_client
                )

                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error getting subscription {subscription_id}: {response}")
                    return None

                if isinstance(response, SubscriptionDetailResponse):
                    return response

                logger.warning(
                    f"Unexpected response type when getting subscription {subscription_id}: {type(response)}"
                )
                return None
        except Exception as e:
            logger.error(f"Failed to get subscription: {e}")
            return None

    async def create_subscription_with_payment(
        self, user_id: int, plan_id: int, return_url: str, token: str, trial_period_days: Optional[int] = None
    ) -> SubscriptionWithPaymentResponse:
        """
        Create subscription with payment

        Args:
            user_id: User ID
            plan_id: Plan ID
            return_url: Return URL after payment
            token: Authentication token
            trial_period_days: Optional trial period days (only for users without successful payments)

        Returns:
            SubscriptionWithPaymentResponse with payment details

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                # Create request body (trial_period_days removed from schema)
                request_body = SubscriptionWithPaymentRequest(
                    user_id=user_id,
                    plan_id=plan_id,
                    return_url=return_url,
                )

                # Используем asyncio_detailed для получения полного Response с status_code
                response_obj = await create_subscription_with_payment_api_v1_subscriptions_create_with_payment_post.asyncio_detailed(
                    client=auth_client,
                    body=request_body,
                )

                # Проверяем статус ответа
                if response_obj.status_code == 200:
                    # Happy path: return subscription with payment
                    if isinstance(response_obj.parsed, SubscriptionWithPaymentResponse):
                        return response_obj.parsed
                    else:
                        logger.error(f"Unexpected parsed type for 200 response: {type(response_obj.parsed)}")
                        raise Exception("Failed to create subscription: unexpected response type")

                elif response_obj.status_code == 422:
                    # Validation error
                    if isinstance(response_obj.parsed, HTTPValidationError):
                        logger.error(f"Validation error creating subscription: {response_obj.parsed}")
                        raise Exception(f"Validation error: {response_obj.parsed}")
                    else:
                        logger.error(f"Unexpected parsed type for 422 response: {type(response_obj.parsed)}")
                        raise Exception("Failed to create subscription: validation error")

                elif response_obj.status_code == 400:
                    try:
                        import json

                        error_data = json.loads(response_obj.content.decode("utf-8"))
                        error_detail = error_data.get("detail", "Business logic error")
                        logger.warning(f"Business logic error (400) creating subscription: {error_detail}")
                        # Пробрасываем оригинальное сообщение об ошибке
                        raise Exception(error_detail)
                    except json.JSONDecodeError:
                        error_detail = response_obj.content.decode("utf-8", errors="ignore")
                        logger.warning(f"Business logic error (400) creating subscription (non-JSON): {error_detail}")
                        raise Exception(error_detail)
                    except Exception as decode_error:
                        logger.error(f"Failed to decode 400 error response: {decode_error}")
                        raise Exception("Failed to create subscription: business logic error")

                else:

                    logger.error(
                        f"Unexpected status code {response_obj.status_code} when creating subscription. "
                        f"Content: {response_obj.content.decode('utf-8', errors='ignore')}"
                    )
                    raise Exception(f"Failed to create subscription: unexpected status code {response_obj.status_code}")
        except Exception as e:
            logger.error(f"Failed to create subscription with payment: {e}")
            raise

    async def check_trial_eligibility(self, user_id: int, token: str) -> TrialEligibilityResponse:
        """
        Check if trial period is available for user

        Args:
            user_id: User ID
            token: Authentication token

        Returns:
            TrialEligibilityResponse with eligibility status

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                response = (
                    await check_trial_eligibility_api_v1_subscriptions_check_trial_eligibility_user_id_get.asyncio(
                        user_id=user_id, client=auth_client
                    )
                )

                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error checking trial eligibility for user {user_id}: {response}")
                    raise Exception(f"Validation error: {response}")

                if isinstance(response, TrialEligibilityResponse):
                    return response

                logger.error(f"Invalid response when checking trial eligibility: {type(response)}")
                raise Exception("Failed to check trial eligibility: invalid response")
        except Exception as e:
            logger.error(f"Failed to check trial eligibility: {e}")
            raise

    async def create_trial_subscription(self, user_id: int, plan_id: int, token: str) -> CreateTrialResponse:
        """
        Create subscription with trial period

        Args:
            user_id: User ID
            plan_id: Plan ID
            token: Authentication token

        Returns:
            CreateTrialResponse with trial subscription details

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                request_body = CreateTrialRequest(user_id=user_id, plan_id=plan_id)

                response_obj = await create_trial_subscription_api_v1_subscriptions_create_trial_post.asyncio_detailed(
                    client=auth_client, body=request_body
                )

                # Check status code
                if response_obj.status_code == 200:
                    if isinstance(response_obj.parsed, CreateTrialResponse):
                        return response_obj.parsed
                    else:
                        logger.error(f"Unexpected parsed type for 200 response: {type(response_obj.parsed)}")
                        raise Exception("Failed to create trial subscription: unexpected response type")

                elif response_obj.status_code == 422:
                    if isinstance(response_obj.parsed, HTTPValidationError):
                        logger.error(f"Validation error creating trial subscription: {response_obj.parsed}")
                        raise Exception(f"Validation error: {response_obj.parsed}")
                    else:
                        logger.error(f"Unexpected parsed type for 422 response: {type(response_obj.parsed)}")
                        raise Exception("Failed to create trial subscription: validation error")

                elif response_obj.status_code == 400:
                    # Business logic error
                    try:
                        import json

                        error_data = json.loads(response_obj.content.decode("utf-8"))
                        error_detail = error_data.get("detail", "Business logic error")
                        logger.warning(f"Business logic error (400) creating trial subscription: {error_detail}")
                        raise Exception(error_detail)
                    except json.JSONDecodeError:
                        error_detail = response_obj.content.decode("utf-8", errors="ignore")
                        logger.warning(
                            f"Business logic error (400) creating trial subscription (non-JSON): {error_detail}"
                        )
                        raise Exception(error_detail)
                    except Exception as decode_error:
                        logger.error(f"Failed to decode 400 error response: {decode_error}")
                        raise Exception("Failed to create trial subscription: business logic error")

                else:
                    logger.error(
                        f"Unexpected status code {response_obj.status_code} when creating trial subscription. "
                        f"Content: {response_obj.content.decode('utf-8', errors='ignore')}"
                    )
                    raise Exception(
                        f"Failed to create trial subscription: unexpected status code {response_obj.status_code}"
                    )
        except Exception as e:
            logger.error(f"Failed to create trial subscription: {e}")
            raise

    async def cancel_subscription(
        self, subscription_id: int, token: str, with_refund: bool = False
    ) -> SubscriptionResponse:
        """
        Cancel subscription

        Args:
            subscription_id: Subscription ID
            token: Authentication token
            with_refund: Выполнить возврат средств. Если True - подписка отменяется сразу с возвратом.
                         Если False - подписка активна до end_date без возврата (по умолчанию)

        Returns:
            Cancelled subscription

        Raises:
            Exception: If operation fails
        """
        from billing_core_api_client.models.cancel_subscription_request import CancelSubscriptionRequest

        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                # Создаем запрос с параметром with_refund
                request_body = CancelSubscriptionRequest(with_refund=with_refund)

                response = await cancel_subscription_api_v1_subscriptions_subscription_id_cancel_patch.asyncio(
                    subscription_id=subscription_id, body=request_body, client=auth_client
                )

                # Check for validation errors
                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error canceling subscription {subscription_id}: {response}")
                    raise Exception(f"Validation error: {response}")

                # Happy path: return cancelled subscription
                if isinstance(response, SubscriptionResponse):
                    return response

                # Invalid response
                logger.error(f"Invalid response when canceling subscription: {type(response)}")
                raise Exception("Failed to cancel subscription: invalid response")
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise

    async def apply_promotion_to_subscription(
        self, subscription_id: int, promotion_code: str, token: str
    ) -> ApplyPromotionResponse:
        """
        Apply promotion code to active subscription

        Args:
            subscription_id: Subscription ID
            promotion_code: Promotion code
            token: Authentication token

        Returns:
            ApplyPromotionResponse with promotion application details

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                request_body = ApplyPromotionRequest(promotion_code=promotion_code)

                response_obj = await apply_promotion_to_subscription_api_v1_subscriptions_subscription_id_apply_promotion_post.asyncio_detailed(
                    subscription_id=subscription_id, body=request_body, client=auth_client
                )

                # Check status code
                if response_obj.status_code == 200:
                    if isinstance(response_obj.parsed, ApplyPromotionResponse):
                        return response_obj.parsed
                    else:
                        logger.error(f"Unexpected parsed type for 200 response: {type(response_obj.parsed)}")
                        raise Exception("Failed to apply promotion: unexpected response type")

                elif response_obj.status_code == 422:
                    if isinstance(response_obj.parsed, HTTPValidationError):
                        logger.error(f"Validation error applying promotion: {response_obj.parsed}")
                        raise Exception(f"Validation error: {response_obj.parsed}")
                    else:
                        logger.error(f"Unexpected parsed type for 422 response: {type(response_obj.parsed)}")
                        raise Exception("Failed to apply promotion: validation error")

                elif response_obj.status_code == 400:
                    try:
                        import json

                        error_data = json.loads(response_obj.content.decode("utf-8"))
                        error_detail = error_data.get("detail", "Business logic error")
                        logger.warning(f"Business logic error (400) applying promotion: {error_detail}")
                        raise Exception(error_detail)
                    except json.JSONDecodeError:
                        error_detail = response_obj.content.decode("utf-8", errors="ignore")
                        logger.warning(f"Business logic error (400) applying promotion (non-JSON): {error_detail}")
                        raise Exception(error_detail)
                    except Exception as decode_error:
                        logger.error(f"Failed to decode 400 error response: {decode_error}")
                        raise Exception("Failed to apply promotion: business logic error")

                else:
                    logger.error(
                        f"Unexpected status code {response_obj.status_code} when applying promotion. "
                        f"Content: {response_obj.content.decode('utf-8', errors='ignore')}"
                    )
                    raise Exception(f"Failed to apply promotion: unexpected status code {response_obj.status_code}")
        except Exception as e:
            logger.error(f"Failed to apply promotion: {e}")
            raise
