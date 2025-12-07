"""
Social 应用层服务

负责协调领域对象、仓储和基础设施，处理应用逻辑。
管理事务边界和生命周期。
"""
from typing import List, Optional, Dict, Any
import traceback

from app_social.domain.aggregate.post_aggregate import Post
from app_social.domain.aggregate.conversation_aggregate import Conversation
from app_social.domain.value_objects.social_value_objects import (
    PostContent, PostId, PostVisibility, MessageContent, ConversationId, ConversationType
)
from app_social.infrastructure.database.repository_impl.post_repository_impl import PostRepositoryImpl
from app_social.infrastructure.database.repository_impl.conversation_repository_impl import ConversationRepositoryImpl
from app_social.infrastructure.database.dao_impl.sqlalchemy_post_dao import SqlAlchemyPostDao
from app_social.infrastructure.database.dao_impl.sqlalchemy_conversation_dao import SqlAlchemyConversationDao
from app_social.infrastructure.database.dao_impl.sqlalchemy_message_dao import SqlAlchemyMessageDao
from shared.database.core import SessionLocal
from shared.event_bus import get_event_bus

class SocialService:
    """社交模块应用服务"""
    
    def __init__(self):
        self._event_bus = get_event_bus()
    
    # ==================== 帖子管理 ====================
    
    def create_post(
        self,
        author_id: str,
        title: str,
        content: str,
        media_urls: List[str] = None,
        tags: List[str] = None,
        visibility: str = "public",
        trip_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建帖子"""
        session = SessionLocal()
        try:
            # 1. 初始化仓储
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            # 2. 创建领域对象
            post_content = PostContent(
                title=title,
                text=content,
                images=tuple(media_urls or []),
                tags=tuple(tags or [])
            )
            
            try:
                vis_enum = PostVisibility(visibility)
            except ValueError:
                raise ValueError(f"Invalid visibility: {visibility}")
            
            post = Post.create(
                author_id=author_id,
                content=post_content,
                visibility=vis_enum,
                trip_id=trip_id
            )
            
            # 3. 持久化
            post_repo.save(post)
            
            # 4. 发布领域事件
            events = post.pop_events()
            self._event_bus.publish_all(events)
            
            # 5. 提交事务
            session.commit()
            
            return {
                "post_id": post.id.value,
                "created_at": post.created_at.isoformat()
            }
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_post(
        self,
        post_id: str,
        operator_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        media_urls: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """更新帖子内容"""
        session = SessionLocal()
        try:
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            post = post_repo.find_by_id(PostId(post_id))
            if not post:
                raise ValueError("Post not found")
            
            if not post.can_be_edited_by(operator_id):
                raise ValueError("Permission denied")
            
            # 构造新的 PostContent
            current_content = post.content
            new_content = PostContent(
                title=title if title is not None else current_content.title,
                text=content if content is not None else current_content.text,
                images=tuple(media_urls) if media_urls is not None else current_content.images,
                tags=tuple(tags) if tags is not None else current_content.tags
            )
            
            post.update_content(new_content)
            
            post_repo.save(post)
            self._event_bus.publish_all(post.pop_events())
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_post(self, post_id: str, operator_id: str) -> None:
        """删除帖子"""
        session = SessionLocal()
        try:
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            post = post_repo.find_by_id(PostId(post_id))
            if not post:
                raise ValueError("Post not found")
            
            if not post.can_be_edited_by(operator_id):
                 # 这里简化处理，实际上管理员也可能删除，暂时只允许作者删除
                raise ValueError("Permission denied")
            
            post.soft_delete()
            
            post_repo.save(post)
            self._event_bus.publish_all(post.pop_events())
            session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def like_post(self, post_id: str, user_id: str) -> bool:
        """点赞/取消点赞"""
        session = SessionLocal()
        try:
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            post = post_repo.find_by_id(PostId(post_id))
            if not post:
                raise ValueError("Post not found")
            
            if post.is_liked_by(user_id):
                result = post.unlike(user_id)
                action = "unliked"
            else:
                result = post.like(user_id)
                action = "liked"
            
            if result:
                post_repo.save(post)
                self._event_bus.publish_all(post.pop_events())
                session.commit()
            
            return action == "liked"
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_comment(
        self,
        post_id: str,
        user_id: str,
        content: str,
        parent_comment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """发表评论"""
        session = SessionLocal()
        try:
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            post = post_repo.find_by_id(PostId(post_id))
            if not post:
                raise ValueError("Post not found")
            
            comment = post.add_comment(
                commenter_id=user_id,
                content=content,
                parent_comment_id=parent_comment_id
            )
            
            post_repo.save(post)
            self._event_bus.publish_all(post.pop_events())
            session.commit()
            
            return {
                "comment_id": comment.comment_id,
                "created_at": comment.created_at.isoformat()
            }
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_public_feed(self, limit: int = 20, offset: int = 0, tags: List[str] = None) -> List[Dict[str, Any]]:
        """获取公开帖子流"""
        session = SessionLocal()
        try:
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            posts = post_repo.find_public_feed(limit, offset, tags)
            
            return [self._post_to_dto(p) for p in posts]
        finally:
            session.close()
            
    def get_post_detail(self, post_id: str, viewer_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取帖子详情"""
        session = SessionLocal()
        try:
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            post = post_repo.find_by_id(PostId(post_id))
            if not post:
                return None
            
            if not post.can_be_viewed_by(viewer_id or ""):
                # TODO: 更好的权限处理，也许应该区分 not found 和 permission denied
                 raise ValueError("Permission denied")

            return self._post_to_dto(post, viewer_id)
        finally:
            session.close()

    def get_user_posts(self, user_id: str, viewer_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户的帖子"""
        session = SessionLocal()
        try:
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            # 这里简化处理，全部查出来再过滤可见性，实际应该在数据库层过滤
            posts = post_repo.find_by_author(user_id, limit=limit, offset=offset)
            
            visible_posts = []
            for p in posts:
                if p.can_be_viewed_by(viewer_id or ""):
                    visible_posts.append(p)
            
            return [self._post_to_dto(p, viewer_id) for p in visible_posts]
        finally:
            session.close()

    def _post_to_dto(self, post: Post, viewer_id: Optional[str] = None) -> Dict[str, Any]:
        """将 Post 聚合根转换为 DTO"""
        return {
            "id": post.id.value,
            "author_id": post.author_id,
            "title": post.content.title,
            "content": post.content.text,
            "media_urls": post.content.images,
            "tags": post.content.tags,
            "visibility": post.visibility.value,
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat(),
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "is_liked": post.is_liked_by(viewer_id) if viewer_id else False,
            "comments": [
                {
                    "id": c.comment_id,
                    "author_id": c.author_id,
                    "content": c.content,
                    "created_at": c.created_at.isoformat(),
                    "parent_id": c.parent_id
                } for c in post.comments
            ]
        }

    # ==================== 会话管理 ====================
    
    def create_private_chat(self, user1_id: str, user2_id: str) -> Dict[str, Any]:
        """创建私聊"""
        session = SessionLocal()
        try:
            conv_dao = SqlAlchemyConversationDao(session)
            msg_dao = SqlAlchemyMessageDao(session)
            conv_repo = ConversationRepositoryImpl(conv_dao, msg_dao)
            
            # 检查是否已存在
            existing = conv_repo.find_by_participants(user1_id, user2_id)
            if existing:
                return {"conversation_id": existing.id.value, "is_new": False}
            
            conv = Conversation.create_private(user1_id, user2_id)
            
            conv_repo.save(conv)
            self._event_bus.publish_all(conv.pop_events())
            session.commit()
            
            return {"conversation_id": conv.id.value, "is_new": True}
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def send_message(
        self,
        conversation_id: str,
        sender_id: str,
        content: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """发送消息"""
        session = SessionLocal()
        try:
            conv_dao = SqlAlchemyConversationDao(session)
            msg_dao = SqlAlchemyMessageDao(session)
            conv_repo = ConversationRepositoryImpl(conv_dao, msg_dao)
            
            conv = conv_repo.find_by_id(ConversationId(conversation_id))
            if not conv:
                raise ValueError("Conversation not found")
            
            msg_content = MessageContent(text=content, message_type=message_type)
            message = conv.send_message(sender_id, msg_content)
            
            conv_repo.save(conv)
            self._event_bus.publish_all(conv.pop_events())
            session.commit()
            
            return {
                "message_id": message.message_id,
                "sent_at": message.sent_at.isoformat()
            }
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的会话列表"""
        session = SessionLocal()
        try:
            conv_dao = SqlAlchemyConversationDao(session)
            msg_dao = SqlAlchemyMessageDao(session)
            conv_repo = ConversationRepositoryImpl(conv_dao, msg_dao)
            
            convs = conv_repo.find_by_user(user_id)
            
            results = []
            for conv in convs:
                last_msg = conv.messages[-1] if conv.messages else None
                results.append({
                    "id": conv.id.value,
                    "type": conv.conversation_type.value,
                    "title": conv.title,
                    "unread_count": conv.get_unread_count(user_id),
                    "last_message": {
                        "content": last_msg.content.text if last_msg else None,
                        "type": last_msg.content.message_type if last_msg else None,
                        "sent_at": last_msg.sent_at.isoformat() if last_msg else None,
                        "sender_id": last_msg.sender_id if last_msg else None
                    } if last_msg else None,
                    "participants": list(conv.participant_ids)
                })
            return results
        finally:
            session.close()

    def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取会话消息"""
        session = SessionLocal()
        try:
            conv_dao = SqlAlchemyConversationDao(session)
            msg_dao = SqlAlchemyMessageDao(session)
            conv_repo = ConversationRepositoryImpl(conv_dao, msg_dao)
            
            conv = conv_repo.find_by_id(ConversationId(conversation_id))
            if not conv:
                raise ValueError("Conversation not found")
            
            if not conv.is_participant(user_id):
                raise ValueError("Permission denied")
            
            # 标记已读
            # 注意：这里可能会有副作用，改变状态，所以需要 commit
            read_count = conv.mark_as_read(user_id)
            if read_count > 0:
                conv_repo.save(conv)
                self._event_bus.publish_all(conv.pop_events())
                session.commit()
            
            messages = conv.get_recent_messages(limit)
            return [{
                "id": m.message_id,
                "sender_id": m.sender_id,
                "content": m.content.text,
                "type": m.content.message_type,
                "sent_at": m.sent_at.isoformat(),
                "is_read_by_me": m.is_read_by(user_id) # 应该是 True
            } for m in messages]
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
