"""
Promotion service for bot
"""

import logging
import sys
from pathlib import Path

# Add api-client to path
api_client_path = Path(__file__).parent.parent / "api-client"
if str(api_client_path) not in sys.path:
    sys.path.insert(0, str(api_client_path))

from billing_core_api_client.api.promotions import (
    get_available_promotions_api_v1_promotions_available_get,
)
from billing_core_api_client.models import HTTPValidationError, Promotion
from bot.core.api_client import get_authenticated_client

logger = logging.getLogger(__name__)


class PromotionService:
    """Service for promotion operations"""

    async def get_available_promotions(self, token: str) -> list[Promotion]:
        """
        Get available promotions for authenticated user

        Args:
            token: Authentication token

        Returns:
            List of available promotions

        Raises:
            Exception: If operation fails
        """
        auth_client = get_authenticated_client(token)
        try:
            async with auth_client:
                response = await get_available_promotions_api_v1_promotions_available_get.asyncio(client=auth_client)

                if isinstance(response, HTTPValidationError):
                    logger.error(f"Validation error getting available promotions: {response}")
                    raise Exception(f"Validation error: {response}")


                if isinstance(response, list):
                    return response

                logger.warning(f"Unexpected response type when getting available promotions: {type(response)}")
                return []
        except Exception as e:
            logger.error(f"Failed to get available promotions: {e}")
            raise
