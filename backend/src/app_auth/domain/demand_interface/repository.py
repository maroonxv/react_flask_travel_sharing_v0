from abc import ABC, abstractmethod
from typing import Optional
from ..entity.user import User
from ..value_objects.value_objects import UserId, Email

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        pass

    @abstractmethod
    def find_by_id(self, user_id: UserId) -> Optional[User]:
        pass

    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        pass
