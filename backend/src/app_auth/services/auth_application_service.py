"""
认证应用服务 - 应用层

负责协调领域服务和基础设施，处理认证相关的用例。
"""
from typing import Optional, Any, List
from flask import session

from app_auth.domain.domain_service.auth_service import AuthService as DomainAuthService
from app_auth.domain.demand_interface.i_user_repository import IUserRepository
from app_auth.domain.entity.user_entity import User
from app_auth.domain.value_objects.user_value_objects import (
    Username, Email, Password, UserRole, UserId, UserProfile
)
from shared.event_bus import EventBus
from shared.storage.local_file_storage import LocalFileStorageService


class AuthApplicationService:
    """认证应用服务
    
    职责：
    1. 协调 DomainAuthService 完成业务逻辑
    2. 管理 Flask Session (登录/登出)
    3. 发布领域事件
    4. 事务管理 (通过 Repository/DAO 隐式处理，或在此处显式 Commit)
    """
    
    def __init__(
        self,
        domain_auth_service: DomainAuthService,
        user_repository: IUserRepository,
        event_bus: Optional[EventBus] = None
    ):
        """初始化应用服务
        
        Args:
            domain_auth_service: 领域认证服务
            user_repository: 用户仓库 (用于查找聚合根)
            event_bus: 事件总线
        """
        self._domain_service = domain_auth_service
        self._user_repo = user_repository
        self._event_bus = event_bus or EventBus.get_instance()
        self._storage_service = LocalFileStorageService()
    
    def _publish_events(self, user: User) -> None:
        """发布用户聚合根中的领域事件"""
        events = user.pop_events()
        self._event_bus.publish_all(events)
    
    def register(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user"
    ) -> User:
        """用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            role: 角色 (默认 user)
            
        Returns:
            注册成功的用户实体
            
        Raises:
            ValueError: 用户名或邮箱已存在
        """
        # 1. 准备数据 (Value Objects)
        v_username = Username(username)
        v_email = Email(email)
        v_password = Password(password)
        v_role = UserRole.from_string(role)
        
        # 2. 调用领域服务
        user = self._domain_service.register_user(
            username=v_username,
            email=v_email,
            password=v_password,
            role=v_role
        )
        
        # 3. 发布事件 (持久化已在 domain_service 中通过 repo.save 完成)
        self._publish_events(user)
        
        return user
    
    def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[User]:
        """用户登录
        
        Args:
            email: 邮箱
            password: 密码
            ip_address: 客户端IP
            user_agent: 客户端UA
            
        Returns:
            登录成功的用户实体，失败返回 None
        """
        v_email = Email(email)
        v_password = Password(password)
        
        # 调用领域服务进行认证
        user = self._domain_service.authenticate(
            email=v_email,
            password=v_password,
            login_ip=ip_address,
            user_agent=user_agent
        )
        
        if user:
            # 登录成功，写入 Flask Session
            session['user_id'] = user.id.value
            session.permanent = True  # 设置为持久会话
            
            # 发布登录事件 (authenticate 方法内部可能已经添加了事件，这里确保发布)
            self._publish_events(user)
            
            return user
            
        return None
    
    def logout(self) -> None:
        """用户登出
        
        清除 Flask Session。
        """
        session.pop('user_id', None)
        session.pop('user_role', None)  # 如果有存储角色的话
        
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户实体，如果不存在则返回 None
        """
        return self._user_repo.find_by_id(UserId(user_id))
    
    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """搜索用户
        
        Args:
            query: 搜索关键词
            limit: 限制数量
            
        Returns:
            用户列表
        """
        return self._user_repo.search_by_username(query, limit)

    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """修改密码"""
        user = self._user_repo.find_by_id(UserId(user_id))
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
            
        v_old_pass = Password(old_password)
        v_new_pass = Password(new_password)
        
        self._domain_service.change_password(user, v_old_pass, v_new_pass)
        
        # 发布事件
        self._publish_events(user)
        
        return True

    def update_profile(
        self,
        user_id: str,
        location: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
        avatar_file: Optional[Any] = None
    ) -> User:
        """更新个人资料"""
        user = self._user_repo.find_by_id(UserId(user_id))
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # 处理头像上传
        new_avatar_url = avatar_url
        if avatar_file:
            new_avatar_url = self._storage_service.save(avatar_file, sub_folder="avatars")
        
        # 获取当前 profile 属性
        current_profile = user.profile
        
        # 构建新 profile
        new_location = location if location is not None else current_profile.location
        new_bio = bio if bio is not None else current_profile.bio
        final_avatar_url = new_avatar_url if new_avatar_url is not None else current_profile.avatar_url
        
        new_profile_vo = UserProfile(
            avatar_url=final_avatar_url,
            bio=new_bio,
            location=new_location
        )
        
        user.update_profile(new_profile_vo)
        
        self._user_repo.save(user)
        self._publish_events(user)
        
        return user

        
    def request_password_reset(self, email: str) -> None:
        """请求密码重置"""
        v_email = Email(email)
        self._domain_service.request_password_reset(v_email)
        
    def reset_password(self, email: str, new_password: str, token: str) -> None:
        """重置密码 (需配合 Token 验证，演示简化)"""
        # 1. 获取用户
        v_email = Email(email)
        user = self._user_repo.find_by_email(v_email)
        if not user:
            raise ValueError(f"User with email {email} not found")
            
        # 2. 调用领域服务 (Token 验证下沉到领域层)
        v_new_pass = Password(new_password)
        self._domain_service.reset_password(user, v_new_pass, token)
        
        # 3. 发布事件
        self._publish_events(user)
