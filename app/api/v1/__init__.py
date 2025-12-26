"""
API v1 package
"""

from fastapi import APIRouter

from app.api.v1 import auth, auto_payments, payments, ping, plans, promotions, subscriptions, users

api_router = APIRouter()

api_router.include_router(ping.router)
api_router.include_router(users.router)
api_router.include_router(auth.router)
api_router.include_router(subscriptions.router)
api_router.include_router(plans.router)
api_router.include_router(payments.router)
api_router.include_router(auto_payments.router)
api_router.include_router(promotions.router)
