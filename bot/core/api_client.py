"""
API client factory for bot
"""

import sys
from pathlib import Path

import httpx

api_client_path = Path(__file__).parent.parent / "api-client"
if str(api_client_path) not in sys.path:
    sys.path.insert(0, str(api_client_path))

from billing_core_api_client import AuthenticatedClient, Client
from bot.core.config import config

DEFAULT_TIMEOUT = httpx.Timeout(30.0, read=60.0)


def get_api_client() -> Client:
    """Get unauthenticated API client with timeout configuration"""
    return Client(base_url=config.API_BASE_URL, timeout=DEFAULT_TIMEOUT)


def get_authenticated_client(token: str) -> AuthenticatedClient:
    """Get authenticated API client with timeout configuration"""
    return AuthenticatedClient(base_url=config.API_BASE_URL, token=token, timeout=DEFAULT_TIMEOUT)
