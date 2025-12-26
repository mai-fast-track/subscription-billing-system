"""
Ping endpoint
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def ping():
    """
    Ping endpoint - returns pong
    """
    return {"message": "pong"}
