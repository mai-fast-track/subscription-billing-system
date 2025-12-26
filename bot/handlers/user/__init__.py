from aiogram import Router

from . import payments, promo, start, subscriptions

user_router = Router()

user_router.include_router(start.router)
user_router.include_router(subscriptions.router)
user_router.include_router(payments.router)
user_router.include_router(promo.router)

__all__ = ["user_router"]
