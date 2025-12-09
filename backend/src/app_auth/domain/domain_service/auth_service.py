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
from app_auth.domain.demand_interface.i_email_service import IEmailService


class AuthService:
    """认证领域服务 - 无状态
    
    处理需要协调多个对象的认证业务逻辑。
    简单的业务操作应该在聚合根内完成。
    """
    
    def __init__(
        self,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher,
        email_service: IEmailService
    ):
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._email_service = email_service
    
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
    
    # 演示用的 Mock Token
    MOCK_RESET_TOKEN = "MOCK-RESET-TOKEN-12345"
    
    def request_password_reset(self, email: Email) -> None:
        """请求密码重置
        
        查找用户，生成令牌（简化为直接发送通知），并发送邮件。
        
        Args:
            email: 用户邮箱
            
        Raises:
            ValueError: 用户不存在
        """
        user = self._user_repo.find_by_email(email)
        if not user:
            # 为了安全，通常不应明确提示用户不存在，但演示项目可以简化
            raise ValueError(f"User with email '{email.value}' not found")
            
        # 在实际项目中，这里应该生成一个一次性 Token，并保存到数据库或 Redis
        # 这里演示项目简化为直接发送邮件通知
        reset_token = self.MOCK_RESET_TOKEN
        
        self._email_service.send_email(
            to=email.value,
            subject="Password Reset Request",
            content=f"Hello {user.username.value},\n\n"
                    f"You requested a password reset. Use this token: {reset_token}\n"
                    f"Or just imagine clicking a link."
        )
    
    def reset_password(self, user: User, new_password: Password, token: str) -> None:
        """重置密码
        
        由应用层验证令牌后调用。
        
        Args:
            user: 用户实例
            new_password: 新密码
            token: 重置令牌
            
        Raises:
            ValueError: 令牌无效
        """
        # 验证 Token (Mock)
        if token != self.MOCK_RESET_TOKEN:
            raise ValueError("Invalid password reset token")
            
        user.reset_password(new_password, self._password_hasher)
        self._user_repo.save(user)
