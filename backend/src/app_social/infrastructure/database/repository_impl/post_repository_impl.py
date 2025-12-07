"""
帖子仓库实现

实现 IPostRepository 接口。
负责 Post 聚合根及其子实体（Comment, Like, Image, Tag）的持久化。
"""
from typing import List, Optional

from app_social.domain.demand_interface.i_post_repository import IPostRepository
from app_social.domain.aggregate.post_aggregate import Post
from app_social.domain.value_objects.social_value_objects import PostId, PostVisibility
from app_social.infrastructure.database.dao_interface.i_post_dao import IPostDao
from app_social.infrastructure.database.persistent_model.post_po import PostPO, CommentPO, LikePO, PostImagePO, PostTagPO


class PostRepositoryImpl(IPostRepository):
    """帖子仓库实现"""
    
    def __init__(self, post_dao: IPostDao):
        """初始化仓库
        
        Args:
            post_dao: 帖子数据访问对象
        """
        self._post_dao = post_dao
    
    def save(self, post: Post) -> None:
        """保存帖子（新增或更新）"""
        existing_po = self._post_dao.find_by_id(post.id.value)
        
        if existing_po:
            # 更新现有帖子
            existing_po.update_from_domain(post)
            # 更新子实体
            self._sync_comments(existing_po, post)
            self._sync_likes(existing_po, post)
            # images 和 tags 已经在 PostPO.update_from_domain 中通过替换列表的方式更新了
            # 利用 SQLAlchemy 的 cascade='all, delete-orphan' 机制，
            # 替换列表会自动删除旧的关联对象并插入新的，所以这里不需要额外的 sync 方法。
            
            self._post_dao.update(existing_po)
        else:
            # 添加新帖子
            post_po = PostPO.from_domain(post)
            self._post_dao.add(post_po)
    
    def _sync_comments(self, post_po: PostPO, post: Post) -> None:
        """同步评论
        
        Args:
            post_po: 帖子持久化对象
            post: Post 领域实体
        """
        # 获取当前评论ID集合
        existing_comment_ids = {c.id for c in post_po.comments}
        new_comment_ids = {c.comment_id for c in post.comments}
        
        # 删除不再存在的评论
        # 注意：在 SQLAlchemy 中，对于 cascade='all, delete-orphan'，
        # 应该从集合中移除对象，而不是重新赋值列表（虽然重新赋值通常也工作，但移除更明确）
        # 但为了保持代码风格一致性，这里沿用之前的逻辑，
        # 只要 PostPO.comments 配置了 cascade，SQLAlchemy 会处理孤儿删除。
        
        # 这种过滤方式其实是重新创建了一个列表，SQLAlchemy 会比较新旧列表
        post_po.comments = [c for c in post_po.comments if c.id in new_comment_ids]
        
        # 更新或添加评论
        for comment in post.comments:
            existing = next((c for c in post_po.comments if c.id == comment.comment_id), None)
            if existing:
                existing.update_from_domain(comment)
            else:
                post_po.comments.append(CommentPO.from_domain(comment))
    
    def _sync_likes(self, post_po: PostPO, post: Post) -> None:
        """同步点赞
        
        Args:
            post_po: 帖子持久化对象
            post: Post 领域实体
        """
        # 获取当前点赞用户ID集合
        existing_like_user_ids = {l.user_id for l in post_po.likes}
        new_like_user_ids = {l.user_id for l in post.likes}
        
        # 删除取消的点赞
        post_po.likes = [l for l in post_po.likes if l.user_id in new_like_user_ids]
        
        # 添加新点赞
        for like in post.likes:
            if like.user_id not in existing_like_user_ids:
                post_po.likes.append(LikePO.from_domain(like))
    
    def find_by_id(self, post_id: PostId) -> Optional[Post]:
        """根据ID查找帖子"""
        post_po = self._post_dao.find_by_id(post_id.value)
        if post_po:
            return post_po.to_domain()
        return None
    
    def find_by_author(
        self,
        author_id: str,
        include_deleted: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[Post]:
        """查找用户的帖子"""
        post_pos = self._post_dao.find_by_author(
            author_id=author_id,
            include_deleted=include_deleted,
            limit=limit,
            offset=offset
        )
        return [po.to_domain() for po in post_pos]
    
    def find_by_trip(self, trip_id: str) -> Optional[Post]:
        """查找关联旅行的游记"""
        post_po = self._post_dao.find_by_trip(trip_id)
        if post_po:
            return post_po.to_domain()
        return None
    
    def find_public_feed(
        self,
        limit: int = 20,
        offset: int = 0,
        tags: Optional[List[str]] = None
    ) -> List[Post]:
        """获取公开帖子流"""
        post_pos = self._post_dao.find_public_feed(
            limit=limit,
            offset=offset,
            tags=tags
        )
        return [po.to_domain() for po in post_pos]
    
    def find_by_visibility(
        self,
        visibility: PostVisibility,
        limit: int = 20,
        offset: int = 0
    ) -> List[Post]:
        """按可见性查找帖子"""
        post_pos = self._post_dao.find_by_visibility(
            visibility=visibility.value,
            limit=limit,
            offset=offset
        )
        return [po.to_domain() for po in post_pos]
    
    def delete(self, post_id: PostId) -> None:
        """删除帖子（物理删除）"""
        self._post_dao.delete(post_id.value)
    
    def exists(self, post_id: PostId) -> bool:
        """检查帖子是否存在"""
        return self._post_dao.exists(post_id.value)
    
    def count_by_author(self, author_id: str, include_deleted: bool = False) -> int:
        """统计用户的帖子数量"""
        return self._post_dao.count_by_author(author_id, include_deleted)
