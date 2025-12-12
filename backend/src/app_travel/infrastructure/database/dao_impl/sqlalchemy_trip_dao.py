from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, desc, and_, or_, exists

from app_travel.infrastructure.database.dao_interface.i_trip_dao import ITripDao
from app_travel.infrastructure.database.persistent_model.trip_po import TripPO, TripMemberPO

class SqlAlchemyTripDao(ITripDao):
    """基于 SQLAlchemy 的旅行 DAO 实现"""

    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, trip_id: str) -> Optional[TripPO]:
        stmt = select(TripPO).where(TripPO.id == trip_id)
        return self.session.execute(stmt).scalars().first()

    def find_by_member(self, user_id: str, status: Optional[str] = None) -> List[TripPO]:
        """查找用户参与的旅行"""
        stmt = (
            select(TripPO)
            .join(TripMemberPO, TripMemberPO.trip_id == TripPO.id)
            .where(TripMemberPO.user_id == user_id)
        )
        
        if status:
            stmt = stmt.where(TripPO.status == status)
            
        stmt = stmt.order_by(desc(TripPO.start_date))
        return list(self.session.execute(stmt).scalars().all())

    def find_by_creator(self, creator_id: str) -> List[TripPO]:
        stmt = (
            select(TripPO)
            .where(TripPO.creator_id == creator_id)
            .order_by(desc(TripPO.created_at))
        )
        return list(self.session.execute(stmt).scalars().all())

    def find_public(self, limit: int = 20, offset: int = 0, search_query: Optional[str] = None) -> List[TripPO]:
        stmt = select(TripPO).where(TripPO.visibility == 'public')
        
        if search_query:
            search_pattern = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    TripPO.name.ilike(search_pattern),
                    TripPO.description.ilike(search_pattern)
                )
            )
            
        stmt = (
            stmt.order_by(desc(TripPO.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().all())

    def add(self, trip_po: TripPO) -> None:
        self.session.add(trip_po)
        self.session.flush()

    def update(self, trip_po: TripPO) -> None:
        self.session.merge(trip_po)
        self.session.flush()

    def delete(self, trip_id: str) -> None:
        stmt = delete(TripPO).where(TripPO.id == trip_id)
        self.session.execute(stmt)
        self.session.flush()

    def exists(self, trip_id: str) -> bool:
        stmt = select(exists().where(TripPO.id == trip_id))
        return self.session.execute(stmt).scalar()
