"""
用户仓库实现

实现 IUserRepository 接口，通过 IUserDao 进行数据持久化操作。
负责领域模型与持久化模型之间的转换。
"""
from typing import List, Optional
from sqlalchemy.exc import IntegrityError

from app_auth.domain.demand_interface.i_user_repository import IUserRepository
from app_auth.domain.entity.user_entity import User
from app_auth.domain.value_objects.user_value_objects import UserId, Email, Username, UserRole
from app_auth.infrastructure.database.dao_interface.i_user_dao import IUserDao
from app_auth.infrastructure.database.persistent_model.user_po import UserPO


class UserRepositoryImpl(IUserRepository):
    """用户仓库实现"""
    
    def __init__(self, user_dao: IUserDao):
        """初始化仓库
        
        Args:
            user_dao: 用户数据访问对象
        """
        self._user_dao = user_dao
    
    def save(self, user: User) -> None:
        """保存用户（新增或更新）
        
        Args:
            user: 用户聚合根
        """
        # Check for duplicates explicitly to ensure data integrity
        # independent of DB constraints (or if they are missing in test env)
        existing_by_email = self.find_by_email(user.email)
        if existing_by_email and existing_by_email.id != user.id:
            raise IntegrityError("Duplicate email", None, Exception(f"Email {user.email.value} already exists"))

        existing_by_username = self.find_by_username(user.username)
        if existing_by_username and existing_by_username.id != user.id:
            raise IntegrityError("Duplicate username", None, Exception(f"Username {user.username.value} already exists"))

        existing_po = self._user_dao.find_by_id(user.id.value)
        
        if existing_po:
            # 更新现有用户
            existing_po.update_from_domain(user)
            self._user_dao.update(existing_po)
        else:
            # 添加新用户
            user_po = UserPO.from_domain(user)
            self._user_dao.add(user_po)
    
    def find_by_id(self, user_id: UserId) -> Optional[User]:
        """根据ID查找用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户实例，如果不存在则返回 None
        """
        user_po = self._user_dao.find_by_id(user_id.value)
        if user_po:
            return user_po.to_domain()
        return None

    def find_by_ids(self, user_ids: List[UserId]) -> List[User]:
        """根据ID列表查找用户
        
        Args:
            user_ids: 用户ID列表
            
        Returns:
            用户列表
        """
        ids = [uid.value for uid in user_ids]
        user_pos = self._user_dao.find_by_ids(ids)
        return [po.to_domain() for po in user_pos]
    
    def find_by_email(self, email: Email) -> Optional[User]:
        """根据邮箱查找用户
        
        Args:
            email: 邮箱
            
        Returns:
            用户实例，如果不存在则返回 None
        """
        user_po = self._user_dao.find_by_email(email.value)
        if user_po:
            return user_po.to_domain()
        return None
    
    def find_by_username(self, username: Username) -> Optional[User]:
        """根据用户名查找用户
        
        Args:
            username: 用户名
            
        Returns:
            用户实例，如果不存在则返回 None
        """
        user_po = self._user_dao.find_by_username(username.value)
        if user_po:
            return user_po.to_domain()
        return None
    
    def find_by_role(self, role: UserRole) -> List[User]:
        """根据角色查找用户列表
        
        Args:
            role: 用户角色
            
        Returns:
            用户列表
        """
        user_pos = self._user_dao.find_by_role(role.value)
        return [po.to_domain() for po in user_pos]
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """分页查找所有用户
        
        Args:
            limit: 每页数量
            offset: 偏移量
            
        Returns:
            用户列表
        """
        user_pos = self._user_dao.find_all(limit=limit, offset=offset)
        return [po.to_domain() for po in user_pos]
    
    def delete(self, user_id: UserId) -> None:
        """删除用户
        
        Args:
            user_id: 用户ID
        """
        self._user_dao.delete(user_id.value)
    
    def exists_by_email(self, email: Email) -> bool:
        """检查邮箱是否已存在
        
        Args:
            email: 邮箱
            
        Returns:
            是否存在
        """
        return self._user_dao.exists_by_email(email.value)
    
    def exists_by_username(self, username: Username) -> bool:
        """检查用户名是否已存在
        
        Args:
            username: 用户名
            
        Returns:
            是否存在
        """
        return self._user_dao.exists_by_username(username.value)
