"""
Subscription endpoints
"""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.core.database import get_uow
from app.database.unit_of_work import UnitOfWork
from app.schemas.promotion import ApplyPromotionRequest, ApplyPromotionResponse
from app.schemas.subscription import (
    CancelSubscriptionRequest,
    CreateTrialRequest,
    CreateTrialResponse,
    SubscriptionCreateRequestSchema,
    SubscriptionDetailResponse,
    SubscriptionResponse,
    SubscriptionWithPaymentRequest,
    SubscriptionWithPaymentResponse,
    TrialEligibilityResponse,
    UserSubscriptionInfo,
)
from app.services.promotion_service import PromotionService
from app.services.subscription_orchestrator_service import SubscriptionOrchestratorService
from app.services.subscription_plan_service import SubscriptionPlanService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(request: SubscriptionCreateRequestSchema, uow: UnitOfWork = Depends(get_uow)):
    """Создать подписку"""
    async with uow:
        try:
            service = SubscriptionService(uow)
            subscription = await service.create_new_subscription(request)
            return subscription
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/create-with-payment", response_model=SubscriptionWithPaymentResponse)
async def create_subscription_with_payment(request: SubscriptionWithPaymentRequest, uow: UnitOfWork = Depends(get_uow)):
    """Создать подписку с платежом (обычное оформление без промопериода)"""
    async with uow:
        try:
            service = SubscriptionOrchestratorService(uow)
            result = await service.create_subscription_with_payment(request)
            return result
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/check-trial-eligibility/{user_id}", response_model=TrialEligibilityResponse)
async def check_trial_eligibility(user_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Проверить доступность промопериода для пользователя"""
    async with uow:
        try:
            service = SubscriptionOrchestratorService(uow)
            result = await service.check_trial_eligibility(user_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/create-trial", response_model=CreateTrialResponse)
async def create_trial_subscription(request: CreateTrialRequest, uow: UnitOfWork = Depends(get_uow)):
    """Создать подписку с промопериодом"""
    async with uow:
        try:
            service = SubscriptionOrchestratorService(uow)
            result = await service.create_trial_subscription(request)
            return result
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/user/{user_id}/active", response_model=Optional[SubscriptionDetailResponse])
async def get_user_active_subscription(user_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Получить активную подписку пользователя"""
    async with uow:
        try:
            SubscriptionService(uow)
            plan_service = SubscriptionPlanService(uow)

            # Получаем активную подписку напрямую из репозитория для полных данных
            sub_model = await uow.subscriptions.get_active_subscription(user_id)

            if not sub_model:
                return None

            # Получаем план для детального ответа
            plan = await plan_service.get_plan_by_id(sub_model.plan_id)
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План подписки не найден")

            return SubscriptionDetailResponse(
                id=sub_model.id,
                user_id=sub_model.user_id,
                plan_id=sub_model.plan_id,
                status=sub_model.status,
                start_date=sub_model.start_date,
                end_date=sub_model.end_date,
                created_at=sub_model.created_at,
                updated_at=sub_model.updated_at,
                plan=plan,
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/user/{user_id}/all", response_model=UserSubscriptionInfo)
async def get_user_subscriptions(user_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Получить все подписки пользователя"""
    async with uow:
        try:
            service = SubscriptionService(uow)
            subscription_info = await service.get_user_subscription_info(user_id)
            return subscription_info
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{subscription_id}", response_model=SubscriptionDetailResponse)
async def get_subscription(subscription_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Получить подписку по ID"""
    async with uow:
        try:
            subscription_service = SubscriptionService(uow)
            plan_service = SubscriptionPlanService(uow)

            subscription = await subscription_service.get_subscription_by_id(subscription_id)

            if not subscription:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подписка не найдена")

            # Получаем план
            plan = await plan_service.get_plan_by_id(subscription.plan_id)
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План подписки не найден")

            # Получаем модель для полных данных
            sub_model = await uow.subscriptions.get_by_id_or_raise(subscription_id)

            return SubscriptionDetailResponse(
                id=sub_model.id,
                user_id=sub_model.user_id,
                plan_id=sub_model.plan_id,
                status=sub_model.status,
                start_date=sub_model.start_date,
                end_date=sub_model.end_date,
                created_at=sub_model.created_at,
                updated_at=sub_model.updated_at,
                plan=plan,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: int,
    request: CancelSubscriptionRequest = Body(default_factory=lambda: CancelSubscriptionRequest(with_refund=False)),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Отменить подписку

    Query параметры:
    - with_refund=False (по умолчанию): Отмена без возврата, подписка активна до end_date
    - with_refund=True: Отмена с возвратом, подписка отменяется сразу
    """
    async with uow:
        try:
            service = SubscriptionService(uow)
            subscription = await service.cancel_subscription(subscription_id, with_refund=request.with_refund)
            return subscription
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[SubscriptionResponse])
async def get_all_subscriptions(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), uow: UnitOfWork = Depends(get_uow)
):
    """Получить все подписки в системе (с пагинацией)"""
    async with uow:
        try:
            service = SubscriptionService(uow)
            subscriptions = await service.get_all_subscriptions(skip=skip, limit=limit)
            return subscriptions
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{subscription_id}/apply-promotion", response_model=ApplyPromotionResponse)
async def apply_promotion_to_subscription(
    subscription_id: int,
    request: ApplyPromotionRequest,
    uow: UnitOfWork = Depends(get_uow),
):
    """Применить промокод к активной подписке (продлевает end_date на бонусные дни)"""
    async with uow:
        try:
            service = PromotionService(uow)
            result = await service.apply_promotion_to_active_subscription(
                subscription_id=subscription_id,
                promotion_code=request.promotion_code,
            )
            return ApplyPromotionResponse(**result)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
