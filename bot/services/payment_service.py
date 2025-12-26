"""
Payment service for bot
"""

import logging
import sys
from pathlib import Path


api_client_path = Path(__file__).parent.parent / "api-client"
if str(api_client_path) not in sys.path:
    sys.path.insert(0, str(api_client_path))

from billing_core_api_client.api.payments import (
    change_payment_method_api_v1_payments_change_payment_method_post,
    get_user_payments_api_v1_payments_user_user_id_get,
)
from billing_core_api_client.models import ChangePaymentMethodRequest, HTTPValidationError, PaymentCreateResponse
from bot.core.api_client import get_authenticated_client

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for payment operations"""

    async def get_user_payments(self, user_id: int, token: str, skip: int = 0, limit: int = 100) -> list[dict]:
        """
        Get all payments for user with subscription information

        Args:
            user_id: User ID
            token: Authentication token
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of payments with subscription info

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                response = await get_user_payments_api_v1_payments_user_user_id_get.asyncio(
                    user_id=user_id, client=auth_client, skip=skip, limit=limit
                )

                # Check for validation errors
                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error getting payments for user {user_id}: {response}")
                    raise Exception(f"Validation error: {response}")

                # Happy path: return list of payments
                if isinstance(response, list):
                    # Convert to dict for easier handling
                    result = []
                    for payment in response:
                        try:
                            # PaymentWithSubscriptionResponse uses attrs with to_dict() method
                            if hasattr(payment, "to_dict"):
                                result.append(payment.to_dict())
                            elif hasattr(payment, "model_dump"):
                                result.append(payment.model_dump())
                            elif hasattr(payment, "dict"):
                                result.append(payment.dict())
                            elif isinstance(payment, dict):
                                result.append(payment)
                            else:
                                # Try to convert to dict
                                result.append(dict(payment))
                        except Exception as convert_error:
                            logger.warning(
                                f"Error converting payment to dict: {convert_error}, payment type: {type(payment)}"
                            )
                            # Skip this payment if we can't convert it
                            continue
                    return result

                # If response is None or unexpected type, return empty list
                logger.warning(f"Unexpected response type when getting payments: {type(response)}")
                return []
        except Exception as e:
            logger.error(f"Failed to get user payments: {e}")
            raise

    async def change_payment_method(
        self,
        user_id: int,
        token: str,
        return_url: str = "https://t.me/subscription_demo_billing_bot",
        amount: float = 1.0,
    ) -> PaymentCreateResponse:
        """
        Change payment method for auto payments

        Args:
            user_id: User ID
            token: Authentication token
            return_url: URL to return after payment (default: bot link)
            amount: Minimum amount for card binding (default: 1.0 RUB)

        Returns:
            PaymentCreateResponse with confirmation_url

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                request_body = ChangePaymentMethodRequest(user_id=user_id, return_url=return_url, amount=amount)
                response = await change_payment_method_api_v1_payments_change_payment_method_post.asyncio(
                    body=request_body, client=auth_client
                )

                # Check for validation errors
                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error changing payment method for user {user_id}: {response}")
                    raise Exception(f"Validation error: {response}")

                # Happy path: return PaymentCreateResponse
                if isinstance(response, PaymentCreateResponse):
                    return response

                # Unexpected type
                logger.warning(f"Unexpected response type when changing payment method: {type(response)}")
                raise Exception(f"Unexpected response type: {type(response)}")
        except Exception as e:
            logger.error(f"Failed to change payment method for user {user_id}: {e}")
            raise
