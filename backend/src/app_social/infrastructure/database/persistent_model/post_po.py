"""
帖子及相关持久化对象 (PO - Persistent Object)

用于 SQLAlchemy ORM 映射，与数据库表对应。
包含 PostPO, CommentPO, LikePO, PostImagePO, PostTagPO。
"""
from datetime import datetime
from typing import List, Optional, Tuple
import json

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from shared.database.core import Base

from app_social.domain.aggregate.post_aggregate import Post
from app_social.domain.entity.comment_entity import Comment
from app_social.domain.entity.like_entity import Like
from app_social.domain.value_objects.social_value_objects import (
    PostId, PostContent, PostVisibility
)


class LikePO(Base):
    """点赞持久化对象"""
    
    __tablename__ = 'likes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, index=True)
    post_id = Column(String(36), ForeignKey('posts.id'), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关联
    post = relationship('PostPO', back_populates='likes')
    
    def to_domain(self) -> Like:
        """转换为领域实体"""
        return Like(
            user_id=self.user_id,
            post_id=self.post_id,
            created_at=self.created_at
        )
    
    @classmethod
    def from_domain(cls, like: Like) -> 'LikePO':
        """从领域实体创建"""
        return cls(
            user_id=like.user_id,
            post_id=like.post_id,
            created_at=like.created_at
        )


class CommentPO(Base):
    """评论持久化对象"""
    
    __tablename__ = 'comments'
    
    id = Column(String(36), primary_key=True)
    post_id = Column(String(36), ForeignKey('posts.id'), nullable=False, index=True)
    author_id = Column(String(36), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(String(36), nullable=True)  # 回复的评论ID
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # 关联
    post = relationship('PostPO', back_populates='comments')
    
    def to_domain(self) -> Comment:
        """转换为领域实体"""
        return Comment(
            comment_id=self.id,
            post_id=self.post_id,
            author_id=self.author_id,
            content=self.content,
            parent_id=self.parent_id,
            created_at=self.created_at,
            is_deleted=self.is_deleted
        )
    
    @classmethod
    def from_domain(cls, comment: Comment) -> 'CommentPO':
        """从领域实体创建"""
        return cls(
            id=comment.comment_id,
            post_id=comment.post_id,
            author_id=comment.author_id,
            content=comment.content,
            parent_id=comment.parent_id,
            created_at=comment.created_at,
            is_deleted=comment.is_deleted
        )
    
    def update_from_domain(self, comment: Comment) -> None:
        """从领域实体更新"""
        self.content = comment.content
        self.is_deleted = comment.is_deleted


class PostImagePO(Base):
    """帖子图片持久化对象"""
    __tablename__ = 'post_images'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(36), ForeignKey('posts.id'), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
    
    post = relationship('PostPO', back_populates='images')


class PostTagPO(Base):
    """帖子标签持久化对象"""
    __tablename__ = 'post_tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(36), ForeignKey('posts.id'), nullable=False, index=True)
    tag = Column(String(50), nullable=False, index=True)
    
    post = relationship('PostPO', back_populates='tags')


class PostPO(Base):
    """帖子持久化对象 - SQLAlchemy 模型"""
    
    __tablename__ = 'posts'
    
    id = Column(String(36), primary_key=True)
    author_id = Column(String(36), nullable=False, index=True)
    
    # 内容
    title = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)
    # images 和 tags 现已通过关联表实现
    
    # 元数据
    visibility = Column(String(20), nullable=False, default='public')
    trip_id = Column(String(36), nullable=True, index=True)  # 关联旅行
    
    # 状态
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    comments = relationship('CommentPO', back_populates='post', cascade='all, delete-orphan')
    likes = relationship('LikePO', back_populates='post', cascade='all, delete-orphan')
    images = relationship('PostImagePO', back_populates='post', cascade='all, delete-orphan', order_by='PostImagePO.display_order')
    tags = relationship('PostTagPO', back_populates='post', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f"PostPO(id={self.id}, title={self.title[:20]}...)"
    
    def to_domain(self) -> Post:
        """将持久化对象转换为领域实体"""
        image_urls = tuple(img.image_url for img in self.images)
        tag_list = tuple(t.tag for t in self.tags)
        
        content = PostContent(
            title=self.title,
            text=self.text,
            images=image_urls,
            tags=tag_list
        )
        
        domain_comments = [c.to_domain() for c in self.comments]
        domain_likes = [l.to_domain() for l in self.likes]
        
        return Post.reconstitute(
            post_id=PostId(self.id),
            author_id=self.author_id,
            content=content,
            comments=domain_comments,
            likes=domain_likes,
            visibility=PostVisibility.from_string(self.visibility),
            trip_id=self.trip_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_deleted=self.is_deleted
        )
    
    @classmethod
    def from_domain(cls, post: Post) -> 'PostPO':
        """从领域实体创建持久化对象"""
        po = cls(
            id=post.id.value,
            author_id=post.author_id,
            title=post.content.title,
            text=post.content.text,
            visibility=post.visibility.value,
            trip_id=post.trip_id,
            is_deleted=post.is_deleted,
            created_at=post.created_at,
            updated_at=post.updated_at
        )
        
        # 处理关联对象
        po.images = [
            PostImagePO(image_url=url, display_order=idx) 
            for idx, url in enumerate(post.content.images)
        ]
        po.tags = [PostTagPO(tag=tag) for tag in post.content.tags]
        
        po.comments = [CommentPO.from_domain(c) for c in post.comments]
        po.likes = [LikePO.from_domain(l) for l in post.likes]
        
        return po
    
    def update_from_domain(self, post: Post) -> None:
        """从领域实体更新持久化对象"""
        self.title = post.content.title
        self.text = post.content.text
        self.visibility = post.visibility.value
        self.trip_id = post.trip_id
        self.is_deleted = post.is_deleted
        self.updated_at = post.updated_at
        
        # 更新图片：直接替换集合，利用 cascade='all, delete-orphan'
        self.images = [
            PostImagePO(image_url=url, display_order=idx) 
            for idx, url in enumerate(post.content.images)
        ]
        
        # 更新标签：直接替换集合
        self.tags = [PostTagPO(tag=tag) for tag in post.content.tags]
