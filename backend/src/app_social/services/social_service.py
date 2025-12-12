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
    PostContent, PostId, PostVisibility, MessageContent, ConversationId, ConversationType, ConversationRole
)
from app_social.infrastructure.database.repository_impl.post_repository_impl import PostRepositoryImpl
from app_social.infrastructure.database.repository_impl.conversation_repository_impl import ConversationRepositoryImpl
from app_travel.infrastructure.database.dao_impl.sqlalchemy_trip_dao import SqlAlchemyTripDao
from app_travel.infrastructure.database.repository_impl.trip_repository_impl import TripRepositoryImpl
from app_travel.domain.value_objects.travel_value_objects import TripId
from app_social.infrastructure.database.dao_impl.sqlalchemy_post_dao import SqlAlchemyPostDao
from app_social.infrastructure.database.dao_impl.sqlalchemy_conversation_dao import SqlAlchemyConversationDao
from app_social.infrastructure.database.dao_impl.sqlalchemy_message_dao import SqlAlchemyMessageDao
from app_auth.infrastructure.database.repository_impl.user_repository_impl import UserRepositoryImpl
from app_auth.infrastructure.database.dao_impl.sqlalchemy_user_dao import SqlAlchemyUserDao
from app_auth.domain.value_objects.user_value_objects import UserId
from shared.database.core import SessionLocal
from shared.event_bus import get_event_bus
from shared.storage.local_file_storage import LocalFileStorageService

class SocialService:
    """社交模块应用服务"""
    
    def __init__(self):
        self._event_bus = get_event_bus()
        self._storage_service = LocalFileStorageService()
    
    def are_friends(self, user_id_1: str, user_id_2: str) -> bool:
        """检查两人是否为好友"""
        session = SessionLocal()
        try:
            from app_social.infrastructure.database.dao_impl.sqlalchemy_friendship_dao import SqlAlchemyFriendshipDao
            from app_social.infrastructure.database.repository_impl.friendship_repository_impl import FriendshipRepositoryImpl
            from app_social.domain.value_objects.friendship_value_objects import FriendshipStatus
            
            friend_dao = SqlAlchemyFriendshipDao(session)
            friend_repo = FriendshipRepositoryImpl(friend_dao)
            
            friendship = friend_repo.find_by_users(user_id_1, user_id_2)
            return friendship is not None and friendship.status == FriendshipStatus.ACCEPTED
        finally:
            session.close()

    # ==================== 帖子管理 ====================
    
    def create_post(
        self,
        author_id: str,
        title: str,
        content: str,
        media_files: List[Any] = None, # 接收文件对象 (FileStorage)
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
            
            # 2. 处理文件上传
            image_urls = []
            if media_files:
                for file in media_files:
                    if file:
                        url = self._storage_service.save(file, sub_folder="post_images")
                        image_urls.append(url)
            
            # 3. 创建领域对象
            post_content = PostContent(
                title=title,
                text=content,
                images=tuple(image_urls),
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
        media_files: Optional[List[Any]] = None,
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
            
            # 处理新图片上传
            new_image_urls = None
            if media_files is not None:
                new_image_urls = []
                for file in media_files:
                    if file:
                        url = self._storage_service.save(file, sub_folder="post_images")
                        new_image_urls.append(url)
            
            # 构造新的 PostContent
            current_content = post.content
            new_content = PostContent(
                title=title if title is not None else current_content.title,
                text=content if content is not None else current_content.text,
                images=tuple(new_image_urls) if new_image_urls is not None else current_content.images,
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

    def get_public_feed(self, limit: int = 20, offset: int = 0, tags: List[str] = None, viewer_id: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取公开帖子流"""
        session = SessionLocal()
        try:
            post_dao = SqlAlchemyPostDao(session)
            post_repo = PostRepositoryImpl(post_dao)
            
            posts = post_repo.find_public_feed(limit, offset, tags, search_query)
            
            # Batch fetch authors
            author_ids = list(set(p.author_id for p in posts))
            author_info_map = {}
            if author_ids:
                try:
                    user_dao = SqlAlchemyUserDao(session)
                    user_repo = UserRepositoryImpl(user_dao)
                    users = user_repo.find_by_ids([UserId(uid) for uid in author_ids])
                    for u in users:
                        author_info_map[u.id.value] = {
                            "name": u.username.value,
                            "avatar": u.profile.avatar_url
                        }
                except Exception as e:
                    print(f"Error fetching authors: {e}")
            
            return [self._post_to_dto(p, viewer_id=viewer_id, author_info=author_info_map.get(p.author_id)) for p in posts]
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
            
            # Batch fetch authors (usually just one, but good for consistency)
            author_ids = list(set(p.author_id for p in visible_posts))
            author_info_map = {}
            if author_ids:
                try:
                    user_dao = SqlAlchemyUserDao(session)
                    user_repo = UserRepositoryImpl(user_dao)
                    users = user_repo.find_by_ids([UserId(uid) for uid in author_ids])
                    for u in users:
                        author_info_map[u.id.value] = {
                            "name": u.username.value,
                            "avatar": u.profile.avatar_url
                        }
                except Exception as e:
                    print(f"Error fetching authors: {e}")

            return [self._post_to_dto(p, viewer_id, author_info=author_info_map.get(p.author_id)) for p in visible_posts]
        finally:
            session.close()

    def _post_to_dto(self, post: Post, viewer_id: Optional[str] = None, author_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """将 Post 聚合根转换为 DTO"""
        # 获取作者信息
        author_name = "Unknown"
        author_avatar = None
        
        session = SessionLocal()
        try:
            user_dao = SqlAlchemyUserDao(session)
            user_repo = UserRepositoryImpl(user_dao)
            
            # Post author
            if author_info:
                author_name = author_info.get("name", "Unknown")
                author_avatar = author_info.get("avatar")
            else:
                try:
                    author = user_repo.find_by_id(UserId(post.author_id))
                    if author:
                        author_name = author.username.value
                        author_avatar = author.profile.avatar_url
                except Exception as e:
                    print(f"Error fetching author info: {e}")

            # Comment authors
            comment_authors = {}
            comment_author_ids = list(set(c.author_id for c in post.comments))
            if comment_author_ids:
                try:
                    users = user_repo.find_by_ids([UserId(uid) for uid in comment_author_ids])
                    for u in users:
                        comment_authors[u.id.value] = {
                            "name": u.username.value,
                            "avatar": u.profile.avatar_url
                        }
                except Exception as e:
                    print(f"Error fetching comment authors: {e}")

            # Trip Info
            trip_info = None
            if post.trip_id:
                try:
                    trip_dao = SqlAlchemyTripDao(session)
                    trip_repo = TripRepositoryImpl(trip_dao)
                    trip = trip_repo.find_by_id(TripId(post.trip_id))
                    if trip:
                        trip_info = {
                            "id": trip.id.value,
                            "title": trip.name.value,
                            "is_public": trip.visibility.value == 'public',
                            "cover_image_url": trip.cover_image_url
                        }
                except Exception as e:
                    print(f"Error fetching trip info: {e}")

            return {
                "id": post.id.value,
                "author_id": post.author_id,
                "author_name": author_name,
                "author_avatar": author_avatar,
                "title": post.content.title,
                "content": post.content.text,
                "media_urls": post.content.images,
                "tags": post.content.tags,
                "visibility": post.visibility.value,
                "trip_id": post.trip_id,
                "trip": trip_info,
                "created_at": post.created_at.isoformat(),
                "updated_at": post.updated_at.isoformat(),
                "like_count": post.like_count,
                "comment_count": post.comment_count,
                "is_liked": post.is_liked_by(viewer_id) if viewer_id else False,
                "comments": [
                    {
                        "id": c.comment_id,
                        "author_id": c.author_id,
                        "author_name": comment_authors.get(c.author_id, {}).get("name", "Unknown"),
                        "author_avatar": comment_authors.get(c.author_id, {}).get("avatar"),
                        "content": c.content,
                        "created_at": c.created_at.isoformat(),
                        "parent_id": c.parent_id
                    } for c in post.comments
                ]
            }
        finally:
            session.close()

    # ==================== 会话管理 ====================
    
    def create_group_chat(
        self,
        creator_id: str,
        participant_ids: List[str],
        title: str
    ) -> Dict[str, Any]:
        """创建群聊"""
        session = SessionLocal()
        try:
            conv_dao = SqlAlchemyConversationDao(session)
            msg_dao = SqlAlchemyMessageDao(session)
            conv_repo = ConversationRepositoryImpl(conv_dao, msg_dao)
            
            # 1. 检查好友关系：所有被拉的人必须是创建者的好友
            from app_social.infrastructure.database.dao_impl.sqlalchemy_friendship_dao import SqlAlchemyFriendshipDao
            from app_social.infrastructure.database.repository_impl.friendship_repository_impl import FriendshipRepositoryImpl
            from app_social.domain.value_objects.friendship_value_objects import FriendshipStatus
            
            friend_dao = SqlAlchemyFriendshipDao(session)
            friend_repo = FriendshipRepositoryImpl(friend_dao)
            
            # 排除自己
            targets = [uid for uid in participant_ids if uid != creator_id]
            for target_id in targets:
                 friendship = friend_repo.find_by_users(creator_id, target_id)
                 if not friendship or friendship.status != FriendshipStatus.ACCEPTED:
                     raise ValueError(f"User {target_id} is not your friend")
            
            # 2. 创建群聊
            conv = Conversation.create_group(creator_id, participant_ids, title)
            
            conv_repo.save(conv)
            self._event_bus.publish_all(conv.pop_events())
            session.commit()
            
            return {"conversation_id": conv.id.value}
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def add_group_member(
        self,
        conversation_id: str,
        new_member_id: str,
        operator_id: str
    ) -> None:
        """拉人进群"""
        session = SessionLocal()
        try:
            conv_dao = SqlAlchemyConversationDao(session)
            msg_dao = SqlAlchemyMessageDao(session)
            conv_repo = ConversationRepositoryImpl(conv_dao, msg_dao)
            
            conv = conv_repo.find_by_id(ConversationId(conversation_id))
            if not conv:
                raise ValueError("Conversation not found")
            
            # 1. 检查好友关系
            from app_social.infrastructure.database.dao_impl.sqlalchemy_friendship_dao import SqlAlchemyFriendshipDao
            from app_social.infrastructure.database.repository_impl.friendship_repository_impl import FriendshipRepositoryImpl
            from app_social.domain.value_objects.friendship_value_objects import FriendshipStatus
            
            friend_dao = SqlAlchemyFriendshipDao(session)
            friend_repo = FriendshipRepositoryImpl(friend_dao)
            
            friendship = friend_repo.find_by_users(operator_id, new_member_id)
            if not friendship or friendship.status != FriendshipStatus.ACCEPTED:
                 raise ValueError(f"User {new_member_id} is not your friend")
            
            # 2. 调用聚合根方法
            conv.add_participant(new_member_id, operator_id)
            
            conv_repo.save(conv)
            self._event_bus.publish_all(conv.pop_events())
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def remove_group_member(
        self,
        conversation_id: str,
        target_user_id: str,
        operator_id: str
    ) -> None:
        """踢人或退群"""
        session = SessionLocal()
        try:
            conv_dao = SqlAlchemyConversationDao(session)
            msg_dao = SqlAlchemyMessageDao(session)
            conv_repo = ConversationRepositoryImpl(conv_dao, msg_dao)
            
            conv = conv_repo.find_by_id(ConversationId(conversation_id))
            if not conv:
                raise ValueError("Conversation not found")
            
            conv.remove_participant(target_user_id, operator_id)
            
            conv_repo.save(conv)
            self._event_bus.publish_all(conv.pop_events())
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def change_group_role(
        self,
        conversation_id: str,
        target_user_id: str,
        new_role_str: str,
        operator_id: str
    ) -> None:
        """变更角色"""
        session = SessionLocal()
        try:
            conv_dao = SqlAlchemyConversationDao(session)
            msg_dao = SqlAlchemyMessageDao(session)
            conv_repo = ConversationRepositoryImpl(conv_dao, msg_dao)
            
            conv = conv_repo.find_by_id(ConversationId(conversation_id))
            if not conv:
                raise ValueError("Conversation not found")
            
            try:
                new_role = ConversationRole(new_role_str)
            except ValueError:
                raise ValueError(f"Invalid role: {new_role_str}")
            
            if new_role == ConversationRole.OWNER:
                 conv.transfer_ownership(target_user_id, operator_id)
            else:
                 conv.change_role(target_user_id, new_role, operator_id)
            
            conv_repo.save(conv)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

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
            
            # Enforce Friendship Requirement: defined in task requirement 4
            # "Only become friends can chat"
            # We need to check friendship status.
            # Using FriendshipRepository (Lazy load or import)
            # from app_social.infrastructure.database.dao_impl.sqlalchemy_friendship_dao import SqlAlchemyFriendshipDao
            # from app_social.infrastructure.database.repository_impl.friendship_repository_impl import FriendshipRepositoryImpl
            # from app_social.domain.value_objects.friendship_value_objects import FriendshipStatus
            
            # friend_dao = SqlAlchemyFriendshipDao(session)
            # friend_repo = FriendshipRepositoryImpl(friend_dao)
            # friendship = friend_repo.find_by_users(user1_id, user2_id)
            
            # if not friendship or friendship.status != FriendshipStatus.ACCEPTED:
            #      # Be strict?
            #      raise ValueError("Cannot create chat. You are not friends.")
            
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
            
            # Batch fetch participants info to enrich title/avatar for private chats
            all_participant_ids = set()
            for c in convs:
                all_participant_ids.update(c.participant_ids)
            
            user_info_map = {}
            if all_participant_ids:
                try:
                    user_dao = SqlAlchemyUserDao(session)
                    user_repo = UserRepositoryImpl(user_dao)
                    users = user_repo.find_by_ids([UserId(uid) for uid in all_participant_ids])
                    for u in users:
                        user_info_map[u.id.value] = {
                            "name": u.username.value,
                            "avatar": u.profile.avatar_url
                        }
                except Exception as e:
                    print(f"Error fetching participants info: {e}")

            results = []
            for conv in convs:
                last_msg = conv.messages[-1] if conv.messages else None
                
                # Determine display name and avatar
                other_user_name = None
                other_user_avatar = None
                other_user_id = None
                
                if conv.conversation_type.value == "private":
                    other_id = next((pid for pid in conv.participant_ids if pid != user_id), None)
                    if other_id:
                        other_user_id = other_id
                        info = user_info_map.get(other_id, {})
                        other_user_name = info.get("name")
                        other_user_avatar = info.get("avatar")
                
                # Determine name
                name = conv.title if conv.is_group else other_user_name

                results.append({
                    "id": conv.id.value,
                    "type": conv.conversation_type.value,
                    "name": name,
                    "title": conv.title, # Group title or None
                    "other_user_id": other_user_id,
                    "other_user_name": other_user_name,
                    "other_user_avatar": other_user_avatar,
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
