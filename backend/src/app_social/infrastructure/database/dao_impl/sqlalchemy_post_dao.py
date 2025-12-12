from typing import List, Optional
import json
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select, delete, desc, and_, exists, func, or_

from app_social.infrastructure.database.dao_interface.i_post_dao import IPostDao
from app_social.infrastructure.database.persistent_model.post_po import PostPO, PostTagPO

class SqlAlchemyPostDao(IPostDao):
    """基于 SQLAlchemy 的帖子 DAO 实现"""

    def __init__(self, session: Session):
        self.session = session

    def _get_base_query(self):
        """获取基础查询，包含预加载配置"""
        return select(PostPO).options(
            selectinload(PostPO.comments),
            selectinload(PostPO.likes),
            selectinload(PostPO.images),
            selectinload(PostPO.tags)
        )

    def find_by_id(self, post_id: str) -> Optional[PostPO]:
        stmt = self._get_base_query().where(PostPO.id == post_id)
        return self.session.execute(stmt).scalars().unique().first()

    def find_by_author(
        self,
        author_id: str,
        include_deleted: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[PostPO]:
        stmt = self._get_base_query().where(PostPO.author_id == author_id)
        
        if not include_deleted:
            stmt = stmt.where(PostPO.is_deleted == False)
            
        stmt = stmt.order_by(desc(PostPO.created_at)).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().unique().all())

    def find_by_trip(self, trip_id: str) -> Optional[PostPO]:
        stmt = (
            self._get_base_query()
            .where(
                and_(
                    PostPO.trip_id == trip_id,
                    PostPO.is_deleted == False
                )
            )
        )
        return self.session.execute(stmt).scalars().unique().first()

    def find_public_feed(
        self,
        limit: int = 20,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None
    ) -> List[PostPO]:
        stmt = (
            self._get_base_query()
            .where(
                and_(
                    PostPO.visibility == 'public',
                    PostPO.is_deleted == False
                )
            )
        )
        
        if tags:
            # 标签过滤：任一标签匹配即可
            # 使用 PostPO.tags.any(PostTagPO.tag.in_(tags))
            stmt = stmt.where(PostPO.tags.any(PostTagPO.tag.in_(tags)))

        if search_query:
            search_pattern = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    PostPO.title.ilike(search_pattern),
                    PostPO.text.ilike(search_pattern)
                )
            )
            
        stmt = stmt.order_by(desc(PostPO.created_at)).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().unique().all())

    def find_by_visibility(
        self,
        visibility: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[PostPO]:
        stmt = (
            self._get_base_query()
            .where(
                and_(
                    PostPO.visibility == visibility,
                    PostPO.is_deleted == False
                )
            )
            .order_by(desc(PostPO.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars().unique().all())

    def add(self, post_po: PostPO) -> None:
        self.session.add(post_po)
        self.session.flush() # Explicit flush to avoid pending state issues

    def update(self, post_po: PostPO) -> None:
        self.session.merge(post_po)
        self.session.flush() # Explicit flush to avoid pending state issues

    def delete(self, post_id: str) -> None:
        # 物理删除
        stmt = delete(PostPO).where(PostPO.id == post_id)
        self.session.execute(stmt)
        self.session.flush() # Explicit flush to avoid pending state issues

    def exists(self, post_id: str) -> bool:
        stmt = select(exists().where(PostPO.id == post_id))
        return self.session.execute(stmt).scalar()

    def count_by_author(self, author_id: str, include_deleted: bool = False) -> int:
        stmt = select(func.count()).select_from(PostPO).where(PostPO.author_id == author_id)
        if not include_deleted:
            stmt = stmt.where(PostPO.is_deleted == False)
        return self.session.execute(stmt).scalar()
