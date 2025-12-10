from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, exists

from app_auth.infrastructure.database.dao_interface.i_user_dao import IUserDao
from app_auth.infrastructure.database.persistent_model.user_po import UserPO

class SqlAlchemyUserDao(IUserDao):
    """基于 SQLAlchemy 的用户 DAO 实现"""

    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, user_id: str) -> Optional[UserPO]:
        stmt = select(UserPO).where(UserPO.id == user_id)
        return self.session.execute(stmt).scalars().first()

    def find_by_ids(self, user_ids: List[str]) -> List[UserPO]:
        if not user_ids:
            return []
        stmt = select(UserPO).where(UserPO.id.in_(user_ids))
        return list(self.session.execute(stmt).scalars().all())

    def find_by_email(self, email: str) -> Optional[UserPO]:
        stmt = select(UserPO).where(UserPO.email == email)
        return self.session.execute(stmt).scalars().first()

    def find_by_username(self, username: str) -> Optional[UserPO]:
        stmt = select(UserPO).where(UserPO.username == username)
        return self.session.execute(stmt).scalars().first()

    def find_by_role(self, role: str) -> List[UserPO]:
        stmt = select(UserPO).where(UserPO.role == role)
        return list(self.session.execute(stmt).scalars().all())

    def find_all(self, limit: int = 100, offset: int = 0) -> List[UserPO]:
        stmt = select(UserPO).offset(offset).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def add(self, user_po: UserPO) -> None:
        self.session.add(user_po)
        self.session.flush()

    def update(self, user_po: UserPO) -> None:
        self.session.merge(user_po)
        self.session.flush()

    def delete(self, user_id: str) -> None:
        stmt = delete(UserPO).where(UserPO.id == user_id)
        self.session.execute(stmt)
        self.session.flush()

    def exists_by_email(self, email: str) -> bool:
        stmt = select(exists().where(UserPO.email == email))
        return self.session.execute(stmt).scalar()

    def exists_by_username(self, username: str) -> bool:
        stmt = select(exists().where(UserPO.username == username))
        return self.session.execute(stmt).scalar()
