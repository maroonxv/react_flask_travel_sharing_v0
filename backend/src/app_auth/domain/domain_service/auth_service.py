"""
认证领域服务

领域服务特征：
1. 无状态
2. 处理跨聚合操作
3. 协调多个对象完成业务逻辑
"""
from typing import Optional

from app_auth.domain.entity.user_entity import User
from app_auth.domain.value_objects.user_value_objects import (
    Email, Username, Password, UserRole
)
from app_auth.domain.demand_interface.i_user_repository import IUserRepository
from app_auth.domain.demand_interface.i_password_hasher import IPasswordHasher


class AuthService:
    """认证领域服务 - 无状态
    
    处理需要协调多个对象的认证业务逻辑。
    简单的业务操作应该在聚合根内完成。
    """
    
    def __init__(
        self,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher
    ):
        self._user_repo = user_repo
        self._password_hasher = password_hasher
    
    def register_user(
        self,
        username: Username,
        email: Email,
        password: Password,
        role: UserRole = UserRole.USER
    ) -> User:
        """注册新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            role: 用户角色
            
        Returns:
            创建的用户实例
            
        Raises:
            ValueError: 用户名或邮箱已存在
        """
        # 唯一性检查
        if self._user_repo.exists_by_username(username):
            raise ValueError(f"Username '{username.value}' already exists")
        
        if self._user_repo.exists_by_email(email):
            raise ValueError(f"Email '{email.value}' already exists")
        
        # 通过工厂方法创建用户
        user = User.register(
            username=username,
            email=email,
            password=password,
            password_hasher=self._password_hasher,
            role=role
        )
        
        # 持久化
        self._user_repo.save(user)
        
        return user
    
    def authenticate(
        self,
        email: Email,
        password: Password,
        login_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[User]:
        """用户认证
        
        Args:
            email: 邮箱
            password: 密码
            login_ip: 登录IP（可选）
            user_agent: 用户代理（可选）
            
        Returns:
            认证成功返回用户实例，失败返回 None
        """
        user = self._user_repo.find_by_email(email)
        if not user:
            return None
        
        try:
            if user.authenticate(password, self._password_hasher):
                # 记录登录事件
                user.record_login(login_ip=login_ip, user_agent=user_agent)
                # 保存以触发事件
                self._user_repo.save(user)
                return user
        except ValueError:
            # 账户停用等情况
            pass
        
        return None
    
    def change_password(
        self,
        user: User,
        old_password: Password,
        new_password: Password
    ) -> None:
        """更改密码
        
        Args:
            user: 用户实例
            old_password: 旧密码
            new_password: 新密码
            
        Raises:
            ValueError: 旧密码不正确或新旧密码相同
        """
        user.change_password(
            old_password=old_password,
            new_password=new_password,
            password_hasher=self._password_hasher
        )
        self._user_repo.save(user)
    
    def request_password_reset(self, email: Email) -> Optional[User]:
        """请求密码重置
        
        查找用户并返回，由应用层生成重置令牌。
        
        Args:
            email: 用户邮箱
            
        Returns:
            存在则返回用户实例，不存在返回 None
        """
        return self._user_repo.find_by_email(email)
    
    def reset_password(self, user: User, new_password: Password) -> None:
        """重置密码
        
        由应用层验证令牌后调用。
        
        Args:
            user: 用户实例
            new_password: 新密码
        """
        user.reset_password(new_password, self._password_hasher)
        self._user_repo.save(user)
