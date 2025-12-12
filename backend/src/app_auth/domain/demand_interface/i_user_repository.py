"""
用户仓库接口

仓库模式：聚合根的持久化抽象，由基础设施层实现。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from app_auth.domain.entity.user_entity import User
from app_auth.domain.value_objects.user_value_objects import UserId, Email, Username, UserRole


class IUserRepository(ABC):
    """用户仓库接口"""
    
    @abstractmethod
    def save(self, user: User) -> None:
        """保存用户（新增或更新）
        
        Args:
            user: 用户聚合根
        """
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: UserId) -> Optional[User]:
        """根据ID查找用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户实例，如果不存在则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_ids(self, user_ids: List[UserId]) -> List[User]:
        """根据ID列表查找用户
        
        Args:
            user_ids: 用户ID列表
            
        Returns:
            用户列表
        """
        pass
    
    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        """根据邮箱查找用户
        
        Args:
            email: 邮箱
            
        Returns:
            用户实例，如果不存在则返回 None
        """
        pass
    
    @abstractmethod
    def find_by_username(self, username: Username) -> Optional[User]:
        """根据用户名查找用户
        
        Args:
            username: 用户名
            
        Returns:
            用户实例，如果不存在则返回 None
        """
        pass
    
    @abstractmethod
    def search_by_username(self, query: str, limit: int = 20) -> List[User]:
        """根据用户名搜索用户
        
        Args:
            query: 搜索关键词
            limit: 限制数量
            
        Returns:
            用户列表
        """
        pass

    @abstractmethod
    def find_by_role(self, role: UserRole) -> List[User]:
        """根据角色查找用户列表
        
        Args:
            role: 用户角色
            
        Returns:
            用户列表
        """
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """分页查找所有用户
        
        Args:
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: UserId) -> None:
        """删除用户
        
        Args:
            user_id: 用户ID
        """
        pass
    
    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        """检查邮箱是否已存在
        
        Args:
            email: 邮箱
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def exists_by_username(self, username: Username) -> bool:
        """检查用户名是否已存在
        
        Args:
            username: 用户名
            
        Returns:
            是否存在
        """
        pass
