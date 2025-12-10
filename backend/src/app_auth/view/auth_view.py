"""
认证模块视图层

处理认证相关的 HTTP 请求，调用应用层服务，返回 JSON 响应。
"""
from flask import Blueprint, request, jsonify, g, session
from shared.database.core import SessionLocal

# Infrastructure
from app_auth.infrastructure.database.dao_impl.sqlalchemy_user_dao import SqlAlchemyUserDao
from app_auth.infrastructure.database.repository_impl.user_repository_impl import UserRepositoryImpl
from app_auth.infrastructure.external_service.password_hasher_impl import PasswordHasherImpl
from app_auth.infrastructure.external_service.console_email_service import ConsoleEmailService

# Domain
from app_auth.domain.domain_service.auth_service import AuthService as DomainAuthService
from app_auth.domain.entity.user_entity import User

# Application
from app_auth.services.auth_application_service import AuthApplicationService

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# ==================== 依赖注入与会话管理 ====================

@auth_bp.before_request
def create_session():
    """每个请求开始前创建数据库会话"""
    g.session = SessionLocal()

@auth_bp.teardown_request
def shutdown_session(exception=None):
    """请求结束时关闭数据库会话"""
    if hasattr(g, 'session'):
        g.session.close()

def get_auth_service() -> AuthApplicationService:
    """获取 AuthApplicationService 实例
    
    组装依赖：
    AuthAppService -> DomainAuthService -> UserRepository, PasswordHasher, EmailService
                   -> UserRepository -> UserDao -> Session
    """
    # 基础设施
    user_dao = SqlAlchemyUserDao(g.session)
    user_repo = UserRepositoryImpl(user_dao)
    password_hasher = PasswordHasherImpl()
    email_service = ConsoleEmailService()
    
    # 领域服务
    domain_service = DomainAuthService(
        user_repo=user_repo,
        password_hasher=password_hasher,
        email_service=email_service
    )
    
    # 应用服务
    return AuthApplicationService(
        domain_auth_service=domain_service,
        user_repository=user_repo
    )

# ==================== 序列化辅助函数 ====================

def serialize_user(user: User) -> dict:
    """序列化用户对象"""
    return {
        'id': user.id.value,
        'username': user.username.value,
        'email': user.email.value,
        'role': user.role.value,
        'profile': {
            'avatar_url': user.profile.avatar_url,
            'bio': user.profile.bio,
            'location': user.profile.location
        },
        'is_active': user.is_active,
        'is_email_verified': user.is_email_verified,
        'created_at': user.created_at.isoformat(),
        'updated_at': user.updated_at.isoformat()
    }

# ==================== 路由定义 ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    service = get_auth_service()
    
    try:
        user = service.register(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'user')
        )
        # 显式提交事务
        g.session.commit()
        return jsonify(serialize_user(user)), 201
    except ValueError as e:
        g.session.rollback()
        print(f"Registration ValueError: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        g.session.rollback()
        # 记录日志
        print(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    service = get_auth_service()
    
    try:
        # 获取客户端信息
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        user = service.login(
            email=data['email'],
            password=data['password'],
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if user:
            # 显式提交事务（记录登录信息）
            g.session.commit()
            return jsonify(serialize_user(user)), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        g.session.rollback()
        print(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    service = get_auth_service()
    service.logout()
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """获取当前登录用户信息"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    service = get_auth_service()
    user = service.get_user_by_id(user_id)
    
    if user:
        return jsonify(serialize_user(user)), 200
    else:
        # Session 存在但用户不存在（可能被删），清除 Session
        session.pop('user_id', None)
        return jsonify({'error': 'User not found'}), 401

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """修改密码"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.get_json()
    service = get_auth_service()
    
    try:
        service.change_password(
            user_id=user_id,
            old_password=data['old_password'],
            new_password=data['new_password']
        )
        g.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except ValueError as e:
        g.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        g.session.rollback()
        print(f"Change password error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    """请求密码重置"""
    data = request.get_json()
    service = get_auth_service()
    
    try:
        service.request_password_reset(email=data['email'])
        # 即使邮箱不存在，为了安全也通常返回成功，但演示项目如果抛错也可以处理
        # 我们的 Service 实现是抛出 ValueError，这里可以捕获并决定如何返回
        return jsonify({'message': 'If email exists, a reset token has been sent.'}), 200
    except ValueError:
        # 演示模式下，如果希望前端提示用户不存在，可以返回 400
        # 但标准做法是保持 200，避免枚举用户
        # 这里为了演示方便，返回 200
        return jsonify({'message': 'If email exists, a reset token has been sent.'}), 200
    except Exception as e:
        print(f"Request password reset error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/me/profile', methods=['PUT'])
def update_profile():
    """更新个人资料"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    service = get_auth_service()
    
    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            location = request.form.get('location')
            bio = request.form.get('bio')
            avatar_url = request.form.get('avatar_url') # allow manually setting url
            avatar_file = request.files.get('avatar')
        else:
            data = request.get_json()
            location = data.get('location')
            bio = data.get('bio')
            avatar_url = data.get('avatar_url')
            avatar_file = None
        
        # update_profile handles optional params, so None means no change
        # Note: if client sends null in json, data.get returns None.
        # But if key is missing, data.get also returns None.
        # Ideally we should differentiate "set to null" vs "no change".
        # But for this simple app, we assume None means no change.
        # If we want to clear bio, client should send empty string "".
        
        user = service.update_profile(
            user_id=user_id,
            location=location,
            bio=bio,
            avatar_url=avatar_url,
            avatar_file=avatar_file
        )
        g.session.commit()
        return jsonify(serialize_user(user)), 200
    except ValueError as e:
        g.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        g.session.rollback()
        print(f"Update profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    data = request.get_json()
    service = get_auth_service()
    
    try:
        service.reset_password(
            email=data['email'],
            new_password=data['new_password'],
            token=data['token']
        )
        g.session.commit()
        return jsonify({'message': 'Password reset successfully'}), 200
    except ValueError as e:
        g.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        g.session.rollback()
        print(f"Reset password error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
