"""
帖子 DAO 接口

定义帖子持久化对象的数据访问操作。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app_social.infrastructure.database.persistent_model.post_po import PostPO


class IPostDao(ABC):
    """帖子数据访问对象接口"""
    
    @abstractmethod
    def find_by_id(self, post_id: str) -> Optional[PostPO]:
        """根据ID查找帖子
        
        Args:
            post_id: 帖子ID
            
        Returns:
            帖子持久化对象，不存在则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_author(
        self,
        author_id: str,
        include_deleted: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[PostPO]:
        """查找用户的帖子
        
        Args:
            author_id: 作者ID
            include_deleted: 是否包含已删除的帖子
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            帖子持久化对象列表
        """
        pass
    
    @abstractmethod
    def find_by_trip(self, trip_id: str) -> Optional[PostPO]:
        """查找关联旅行的游记
        
        Args:
            trip_id: 旅行ID
            
        Returns:
            帖子持久化对象，不存在则返回 None
        """
        pass
    
    @abstractmethod
    def find_public_feed(
        self,
        limit: int = 20,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None
    ) -> List[PostPO]:
        """获取公开帖子流
        
        Args:
            limit: 每页数量
            offset: 偏移量
            tags: 标签筛选
            search_query: 搜索关键词
            
        Returns:
            帖子持久化对象列表
        """
        pass
    
    @abstractmethod
    def find_by_visibility(
        self,
        visibility: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[PostPO]:
        """按可见性查找帖子
        
        Args:
            visibility: 可见性
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            帖子持久化对象列表
        """
        pass
    
    @abstractmethod
    def add(self, post_po: PostPO) -> None:
        """添加帖子
        
        Args:
            post_po: 帖子持久化对象
        """
        pass
    
    @abstractmethod
    def update(self, post_po: PostPO) -> None:
        """更新帖子
        
        Args:
            post_po: 帖子持久化对象
        """
        pass
    
    @abstractmethod
    def delete(self, post_id: str) -> None:
        """删除帖子（物理删除）
        
        Args:
            post_id: 帖子ID
        """
        pass
    
    @abstractmethod
    def exists(self, post_id: str) -> bool:
        """检查帖子是否存在
        
        Args:
            post_id: 帖子ID
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def count_by_author(self, author_id: str, include_deleted: bool = False) -> int:
        """统计用户的帖子数量
        
        Args:
            author_id: 作者ID
            include_deleted: 是否包含已删除的帖子
            
        Returns:
            帖子数量
        """
        pass
