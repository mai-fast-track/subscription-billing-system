"""
User endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_uow
from app.database.unit_of_work import UnitOfWork
from app.schemas.user import User, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Получить пользователя по ID"""
    async with uow:
        try:
            service = UserService(uow)
            user = await service.get_user_by_id(user_id)
            return user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, uow: UnitOfWork = Depends(get_uow)):
    """Обновить пользователя"""
    async with uow:
        try:
            service = UserService(uow)
            # Получаем пользователя
            user = await service.get_user_by_id(user_id)

            # Обновляем поля
            if user_update.username is not None:
                user = await uow.users.update_user_profile(
                    user_id=user_id,
                    username=user_update.username,
                    first_name=user_update.first_name,
                    last_name=user_update.last_name,
                )

            if user_update.is_active is not None:
                if user_update.is_active:
                    user = await uow.users.activate_user(user_id)
                else:
                    user = await uow.users.deactivate_user(user_id)

            return user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/transfer/{user_id}", response_model=User)
async def transfer_user(user_id: int, new_telegram_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Передать пользователя другому telegram_id"""
    async with uow:
        try:
            service = UserService(uow)
            user = await service.update_user_by_telegram_id(user_id, new_telegram_id)
            return user
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=list[User])
async def list_users(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), uow: UnitOfWork = Depends(get_uow)
):
    """Получить список пользователей с пагинацией"""
    async with uow:
        try:
            service = UserService(uow)
            users = await service.get_all_users(skip=skip, limit=limit)
            return users
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats/count", response_model=dict)
async def get_user_stats(uow: UnitOfWork = Depends(get_uow)):
    """Получить статистику пользователей"""
    async with uow:
        try:
            total_users = await uow.users.count_total_users()
            active_users = await uow.users.count_active_users()

            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
            }
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
