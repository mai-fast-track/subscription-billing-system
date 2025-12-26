"""
Subscription plan endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_uow
from app.database.unit_of_work import UnitOfWork
from app.schemas.subscription import (
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdate,
)
from app.services.subscription_plan_service import SubscriptionPlanService

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[SubscriptionPlanResponse])
async def get_subscription_plans(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), uow: UnitOfWork = Depends(get_uow)
):
    """Получить все доступные планы подписок"""
    async with uow:
        try:
            service = SubscriptionPlanService(uow)
            plans = await service.get_all_plans(skip=skip, limit=limit)
            return plans
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{plan_id}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(plan_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Получить план подписки по ID"""
    async with uow:
        try:
            service = SubscriptionPlanService(uow)
            plan = await service.get_plan_by_id(plan_id)
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План подписки не найден")
            return plan
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=SubscriptionPlanResponse)
async def create_plan(plan_data: SubscriptionPlanCreateRequest, uow: UnitOfWork = Depends(get_uow)):
    """Создать новый план подписки"""
    async with uow:
        try:
            service = SubscriptionPlanService(uow)
            plan = await service.create_plan(plan_data)
            return plan
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_plan(plan_id: int, plan_update: SubscriptionPlanUpdate, uow: UnitOfWork = Depends(get_uow)):
    """Обновить план подписки"""
    async with uow:
        try:
            service = SubscriptionPlanService(uow)
            plan = await service.update_plan(plan_id, plan_update)
            return plan
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{plan_id}")
async def delete_plan(plan_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Удалить план подписки"""
    async with uow:
        try:
            service = SubscriptionPlanService(uow)
            await service.delete_plan(plan_id)
            return {"message": "План подписки удалён"}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
