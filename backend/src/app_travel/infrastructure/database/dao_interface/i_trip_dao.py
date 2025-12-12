"""
旅行 DAO 接口

定义旅行持久化对象的数据访问操作。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app_travel.infrastructure.database.persistent_model.trip_po import TripPO


class ITripDao(ABC):
    """旅行数据访问对象接口"""
    
    @abstractmethod
    def find_by_id(self, trip_id: str) -> Optional[TripPO]:
        """根据ID查找旅行
        
        Args:
            trip_id: 旅行ID
            
        Returns:
            旅行持久化对象，不存在则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_member(self, user_id: str, status: Optional[str] = None) -> List[TripPO]:
        """查找用户参与的旅行
        
        Args:
            user_id: 用户ID
            status: 可选的状态筛选
            
        Returns:
            旅行持久化对象列表
        """
        pass
    
    @abstractmethod
    def find_by_creator(self, creator_id: str) -> List[TripPO]:
        """查找用户创建的旅行
        
        Args:
            creator_id: 创建者ID
            
        Returns:
            旅行持久化对象列表
        """
        pass
    
    @abstractmethod
    def find_public(self, limit: int = 20, offset: int = 0, search_query: Optional[str] = None) -> List[TripPO]:
        """查找公开的旅行
        
        Args:
            limit: 每页数量
            offset: 偏移量
            search_query: 搜索关键词
            
        Returns:
            旅行持久化对象列表
        """
        pass
    
    @abstractmethod
    def add(self, trip_po: TripPO) -> None:
        """添加旅行
        
        Args:
            trip_po: 旅行持久化对象
        """
        pass
    
    @abstractmethod
    def update(self, trip_po: TripPO) -> None:
        """更新旅行
        
        Args:
            trip_po: 旅行持久化对象
        """
        pass
    
    @abstractmethod
    def delete(self, trip_id: str) -> None:
        """删除旅行
        
        Args:
            trip_id: 旅行ID
        """
        pass
    
    @abstractmethod
    def exists(self, trip_id: str) -> bool:
        """检查旅行是否存在
        
        Args:
            trip_id: 旅行ID
            
        Returns:
            是否存在
        """
        pass
