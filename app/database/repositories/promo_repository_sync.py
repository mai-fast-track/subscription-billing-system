"""
Синхронный Promotion repository - работа с промокодами (для Celery)
"""

from app.core.exceptions import PromotionNotFound
from app.database.base_repository_sync import BaseRepositorySync
from app.models.promotion import Promotion


class PromotionRepositorySync(BaseRepositorySync[Promotion]):
    """Синхронный Repository для управления промокодами (для Celery)"""

    def _get_model(self) -> type[Promotion]:
        return Promotion

    def _get_not_found_exception(self, id_: int) -> Exception:
        return PromotionNotFound(id_)
