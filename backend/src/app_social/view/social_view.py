"""
Social 接口层

提供 RESTful API，处理 HTTP 请求，调用应用服务。
"""
from flask import Blueprint, request, jsonify, g, session
from typing import Dict, Any
import logging

from app_social.services.social_service import SocialService

# 创建 Blueprint
social_bp = Blueprint('social', __name__, url_prefix='/api/social')

# 初始化服务
# 注意：在实际应用中，SocialService 可能是通过依赖注入容器获取的
# 这里直接实例化，因为 SocialService 是无状态的（除了 EventBus 单例）
social_service = SocialService()

logger = logging.getLogger(__name__)

def _get_current_user_id() -> str:
    """获取当前用户ID
    
    优先从 session 获取，其次从 g.user_id 获取（如果中间件设置了），最后尝试 header。
    """
    # 1. Try session (standard for this app)
    user_id = session.get('user_id')
    
    # 2. Try g.user_id
    if not user_id:
        user_id = getattr(g, 'user_id', None)
        
    # 3. Try header (dev/test)
    if not user_id:
        # 尝试从 header 获取（仅用于开发/测试，生产环境应使用 JWT 中间件）
        user_id = request.headers.get('X-User-Id')
    
    if not user_id:
        raise ValueError("Unauthorized")
    return str(user_id)

def _handle_error(e: Exception):
    """统一错误处理"""
    logger.error(f"Error: {e}", exc_info=True)
    if isinstance(e, ValueError):
        return jsonify({"error": str(e)}), 400
    return jsonify({"error": "Internal Server Error"}), 500

# ==================== 帖子 API ====================

@social_bp.route('/posts', methods=['POST'])
def create_post():
    """创建帖子"""
    try:
        user_id = _get_current_user_id()
        
        # 检查 Content-Type
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 处理文件上传
            title = request.form.get('title', '')
            content = request.form.get('content', '')
            tags = request.form.getlist('tags') # form中可能是重复键或者json字符串，这里简化假设
            visibility = request.form.get('visibility', 'public')
            trip_id = request.form.get('trip_id')
            media_files = request.files.getlist('media_files')
        else:
            # 处理 JSON 请求 (不支持文件上传)
            data = request.get_json()
            title = data.get('title', '')
            content = data.get('content', '')
            tags = data.get('tags')
            visibility = data.get('visibility', 'public')
            trip_id = data.get('trip_id')
            media_files = None

        result = social_service.create_post(
            author_id=user_id,
            title=title,
            content=content,
            media_files=media_files,
            tags=tags,
            visibility=visibility,
            trip_id=trip_id
        )
        return jsonify(result), 201
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """获取帖子详情"""
    try:
        # 获取当前用户ID（可选，用于判断是否点赞、是否有权限查看）
        try:
            user_id = _get_current_user_id()
        except ValueError:
            user_id = None
            
        result = social_service.get_post_detail(post_id, user_id)
        if not result:
            return jsonify({"error": "Post not found"}), 404
        return jsonify(result), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/posts/<post_id>', methods=['PUT'])
def update_post(post_id):
    """更新帖子"""
    try:
        user_id = _get_current_user_id()
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            title = request.form.get('title')
            content = request.form.get('content')
            tags = request.form.getlist('tags') if 'tags' in request.form else None
            media_files = request.files.getlist('media_files')
            # 如果没有文件，media_files 可能是空列表，这里需要注意 update_post 的逻辑
            # update_post 中 media_files=None 表示不更新，[] 表示清空？
            # 现有的 update_post 逻辑：if media_files is not None -> 更新。
            # request.files.getlist 如果没传 key 返回空列表。
            # 如果我们想区分“没传”和“传了空”，在 multipart 中比较难。
            # 简化逻辑：如果是 multipart，且没有文件，传 None？
            if not media_files and 'media_files' not in request.files:
                 media_files = None
        else:
            data = request.get_json()
            title = data.get('title')
            content = data.get('content')
            tags = data.get('tags')
            media_files = None

        social_service.update_post(
            post_id=post_id,
            operator_id=user_id,
            title=title,
            content=content,
            media_files=media_files,
            tags=tags
        )
        return jsonify({"message": "Updated successfully"}), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """删除帖子"""
    try:
        user_id = _get_current_user_id()
        social_service.delete_post(post_id, user_id)
        return jsonify({"message": "Deleted successfully"}), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    """点赞/取消点赞"""
    try:
        user_id = _get_current_user_id()
        is_liked = social_service.like_post(post_id, user_id)
        return jsonify({"is_liked": is_liked}), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """发表评论"""
    try:
        user_id = _get_current_user_id()
        data = request.get_json()
        
        result = social_service.add_comment(
            post_id=post_id,
            user_id=user_id,
            content=data.get('content', ''),
            parent_comment_id=data.get('parent_comment_id')
        )
        return jsonify(result), 201
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/feed', methods=['GET'])
def get_feed():
    """获取公开流"""
    try:
        # 尝试获取当前用户ID，以便判断是否点赞
        try:
            user_id = _get_current_user_id()
        except ValueError:
            user_id = None
            
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        tags = request.args.getlist('tags')
        search_query = request.args.get('search') or request.args.get('q')
        
        result = social_service.get_public_feed(limit, offset, tags, viewer_id=user_id, search_query=search_query)
        return jsonify(result), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/users/<user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    """获取用户帖子列表"""
    try:
        try:
            viewer_id = _get_current_user_id()
        except ValueError:
            viewer_id = None
            
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        result = social_service.get_user_posts(user_id, viewer_id, limit, offset)
        return jsonify(result), 200
    except Exception as e:
        return _handle_error(e)

# ==================== 会话 API ====================

@social_bp.route('/conversations', methods=['POST'])
def create_conversation():
    """创建会话 (私聊)"""
    try:
        user_id = _get_current_user_id()
        data = request.get_json()
        target_id = data.get('target_id')
        
        if not target_id:
            return jsonify({"error": "target_id is required"}), 400
            
        result = social_service.create_private_chat(user_id, target_id)
        return jsonify(result), 201
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """获取我的会话列表"""
    try:
        user_id = _get_current_user_id()
        result = social_service.get_user_conversations(user_id)
        return jsonify(result), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/conversations/<conv_id>/messages', methods=['POST'])
def send_message(conv_id):
    """发送消息"""
    try:
        user_id = _get_current_user_id()
        data = request.get_json()
        
        result = social_service.send_message(
            conversation_id=conv_id,
            sender_id=user_id,
            content=data.get('content', ''),
            message_type=data.get('type', 'text')
        )
        return jsonify(result), 201
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/conversations/<conv_id>/messages', methods=['GET'])
def get_messages(conv_id):
    """获取会话消息 (并标记已读)"""
    try:
        user_id = _get_current_user_id()
        limit = int(request.args.get('limit', 50))
        
        result = social_service.get_conversation_messages(conv_id, user_id, limit)
        return jsonify(result), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/conversations/group', methods=['POST'])
def create_group_chat():
    """创建群聊"""
    try:
        user_id = _get_current_user_id()
        data = request.get_json()
        title = data.get('title')
        participant_ids = data.get('participant_ids', [])
        
        if not title:
            return jsonify({"error": "Title is required"}), 400
        if not participant_ids:
            return jsonify({"error": "Participants are required"}), 400
            
        result = social_service.create_group_chat(user_id, participant_ids, title)
        return jsonify(result), 201
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/conversations/<conv_id>/participants', methods=['POST'])
def add_group_participant(conv_id):
    """拉人进群"""
    try:
        user_id = _get_current_user_id()
        data = request.get_json()
        new_member_id = data.get('user_id')
        
        if not new_member_id:
            return jsonify({"error": "user_id is required"}), 400
            
        social_service.add_group_member(conv_id, new_member_id, user_id)
        return jsonify({"message": "Participant added"}), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/conversations/<conv_id>/participants/<target_user_id>', methods=['DELETE'])
def remove_group_participant(conv_id, target_user_id):
    """踢人或退群"""
    try:
        user_id = _get_current_user_id()
        social_service.remove_group_member(conv_id, target_user_id, user_id)
        return jsonify({"message": "Participant removed"}), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/conversations/<conv_id>/participants/<target_user_id>/role', methods=['PUT'])
def change_group_role(conv_id, target_user_id):
    """变更角色（任命管理员/转让群主）"""
    try:
        user_id = _get_current_user_id()
        data = request.get_json()
        new_role = data.get('role') # admin, owner, member
        
        if not new_role:
             return jsonify({"error": "role is required"}), 400
             
        social_service.change_group_role(conv_id, target_user_id, new_role, user_id)
        return jsonify({"message": "Role updated"}), 200
    except Exception as e:
        return _handle_error(e)

# ==================== 好友管理 API ====================

from app_social.services.friendship_service import FriendshipService
from app_social.domain.event_handler.friendship_handler import register_friendship_handlers

# 初始化好友服务
friendship_service = FriendshipService()

# 注册事件处理器
try:
    register_friendship_handlers()
except Exception as e:
    logger.error(f"Failed to register friendship handlers: {e}")

@social_bp.route('/friends/requests', methods=['POST'])
def send_friend_request():
    """发送好友请求"""
    try:
        user_id = _get_current_user_id()
        data = request.get_json()
        target_id = data.get('target_user_id')
        
        if not target_id:
            return jsonify({"error": "target_user_id is required"}), 400
            
        result = friendship_service.send_friend_request(user_id, target_id)
        return jsonify(result), 201
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/friends/requests', methods=['GET'])
def get_friend_requests():
    """获取好友请求列表"""
    try:
        user_id = _get_current_user_id()
        type_ = request.args.get('type', 'incoming')
        result = friendship_service.get_pending_requests(user_id, type_)
        return jsonify(result), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/friends/requests/<req_id>/accept', methods=['PUT'])
def accept_friend_request(req_id):
    """接受好友请求"""
    try:
        user_id = _get_current_user_id()
        friendship_service.accept_friend_request(req_id, user_id)
        return jsonify({"message": "Accepted"}), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/friends/requests/<req_id>/reject', methods=['PUT'])
def reject_friend_request(req_id):
    """拒绝好友请求"""
    try:
        user_id = _get_current_user_id()
        friendship_service.reject_friend_request(req_id, user_id)
        return jsonify({"message": "Rejected"}), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/friends', methods=['GET'])
def get_friends():
    """获取好友列表"""
    try:
        user_id = _get_current_user_id()
        # friendship_service.get_friends already returns enriched user data
        friends_data = friendship_service.get_friends(user_id)
        
        return jsonify({"friends": friends_data}), 200
    except Exception as e:
        return _handle_error(e)

@social_bp.route('/friends/<target_id>/status', methods=['GET'])
def get_friendship_status(target_id):
    """获取与某人的好友状态"""
    try:
        user_id = _get_current_user_id()
        result = friendship_service.get_friendship_status(user_id, target_id)
        return jsonify(result), 200
    except Exception as e:
        return _handle_error(e)
