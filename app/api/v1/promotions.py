"""
Promotion endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_uow
from app.core.security import get_current_user
from app.database.unit_of_work import UnitOfWork
from app.schemas.auth import TokenData
from app.schemas.promotion import Promotion, PromotionCreate, PromotionUpdate
from app.services.promotion_service import PromotionService

router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.get("/", response_model=list[Promotion])
async def get_all_promotions(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), uow: UnitOfWork = Depends(get_uow)
):
    """Получить все промокоды с пагинацией"""
    async with uow:
        try:
            service = PromotionService(uow)
            promotions = await service.get_all_promotions(skip=skip, limit=limit)
            return [Promotion.model_validate(promo) for promo in promotions]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/available", response_model=list[Promotion])
async def get_available_promotions(
    current_user: TokenData = Depends(get_current_user), uow: UnitOfWork = Depends(get_uow)
):
    """
    Получить список доступных промокодов для текущего авторизованного пользователя.

    Включает:
    - Общие промокоды (assigned_user_id = None)
    - Личные промокоды пользователя (assigned_user_id = user_id)

    Исключает:
    - Промокоды, которые пользователь уже использовал
    - Неактивные промокоды
    - Промокоды с истекшим сроком действия
    - Промокоды, достигшие лимита использований

    Требует авторизации через JWT токен.
    """
    async with uow:
        try:
            service = PromotionService(uow)
            promotions = await service.get_available_promotions_for_user(current_user.user_id)
            return [Promotion.model_validate(promo) for promo in promotions]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{promotion_id}", response_model=Promotion)
async def get_promotion(promotion_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Получить промокод по ID"""
    async with uow:
        try:
            service = PromotionService(uow)
            promotion = await service.get_promotion_by_id(promotion_id)
            if not promotion:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Промокод не найден")
            return Promotion.model_validate(promotion)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=Promotion)
async def create_promotion(promotion_data: PromotionCreate, uow: UnitOfWork = Depends(get_uow)):
    """Создать новый промокод"""
    async with uow:
        try:
            service = PromotionService(uow)
            promotion = await service.create_promotion(promotion_data)
            return Promotion.model_validate(promotion)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{promotion_id}", response_model=Promotion)
async def update_promotion(promotion_id: int, promotion_update: PromotionUpdate, uow: UnitOfWork = Depends(get_uow)):
    """Обновить промокод"""
    async with uow:
        try:
            service = PromotionService(uow)
            promotion = await service.update_promotion(promotion_id, promotion_update)
            return Promotion.model_validate(promotion)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{promotion_id}")
async def delete_promotion(promotion_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Удалить промокод"""
    async with uow:
        try:
            service = PromotionService(uow)
            await service.delete_promotion(promotion_id)
            return {"message": "Промокод удалён"}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
