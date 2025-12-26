# repository/user_sync.py


from app.core.exceptions import UserNotFound
from app.database.base_repository_sync import BaseRepositorySync
from app.models import User


class UserRepositorySync(BaseRepositorySync[User]):
    """Синхронный Repository для управления пользователями (для Celery)"""

    def _get_model(self) -> type[User]:
        return User

    def _get_not_found_exception(self, id_: int) -> Exception:
        return UserNotFound(id_)

    def get_by_id_or_raise(self, user_id: int) -> User:
        """Получить пользователя по ID или выбросить исключение"""
        user = self.get_by_id(user_id)
        if not user:
            raise UserNotFound(user_id)
        return user
