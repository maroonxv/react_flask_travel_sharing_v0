from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from shared.database.core import Base

class AiConversationPO(Base):
    """AI 会话持久化对象"""
    __tablename__ = 'ai_conversations'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_deleted = Column(Boolean, nullable=False, default=False)
    
    # 关联
    messages = relationship('AiMessagePO', back_populates='conversation', cascade='all, delete-orphan', order_by='AiMessagePO.id')

class AiMessagePO(Base):
    """AI 消息持久化对象"""
    __tablename__ = 'ai_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey('ai_conversations.id'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    attachments_json = Column(Text, nullable=True) # JSON array of attachments
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 关联
    conversation = relationship('AiConversationPO', back_populates='messages')
