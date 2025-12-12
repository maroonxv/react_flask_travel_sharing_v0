"""
用户 DAO 接口

定义用户持久化对象的数据访问操作。
由具体的数据库实现类实现此接口。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app_auth.infrastructure.database.persistent_model.user_po import UserPO


class IUserDao(ABC):
    """用户数据访问对象接口"""
    
    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[UserPO]:
        """根据ID查找用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户持久化对象，不存在则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_ids(self, user_ids: List[str]) -> List[UserPO]:
        """根据ID列表查找用户
        
        Args:
            user_ids: 用户ID列表
            
        Returns:
            用户持久化对象列表
        """
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[UserPO]:
        """根据邮箱查找用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            用户持久化对象，不存在则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[UserPO]:
        """根据用户名查找用户
        
        Args:
            username: 用户名
            
        Returns:
            用户持久化对象，不存在则返回 None
        """
        pass
    
    @abstractmethod
    def search_by_username(self, query: str, limit: int = 20) -> List[UserPO]:
        """根据用户名模糊搜索用户
        
        Args:
            query: 搜索关键词
            limit: 限制数量
            
        Returns:
            用户持久化对象列表
        """
        pass
    
    @abstractmethod
    def find_by_role(self, role: str) -> List[UserPO]:
        """根据角色查找用户列表
        
        Args:
            role: 用户角色
            
        Returns:
            用户持久化对象列表
        """
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[UserPO]:
        """分页查找所有用户
        
        Args:
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            用户持久化对象列表
        """
        pass
    
    @abstractmethod
    def add(self, user_po: UserPO) -> None:
        """添加用户
        
        Args:
            user_po: 用户持久化对象
        """
        pass
    
    @abstractmethod
    def update(self, user_po: UserPO) -> None:
        """更新用户
        
        Args:
            user_po: 用户持久化对象
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> None:
        """删除用户
        
        Args:
            user_id: 用户ID
        """
        pass
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否已存在
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def exists_by_username(self, username: str) -> bool:
        """检查用户名是否已存在
        
        Args:
            username: 用户名
            
        Returns:
            是否存在
        """
        pass