from typing import List, Optional
from datetime import datetime
import uuid

from app_ai.domain.entity.ai_message import AiMessage
from app_ai.domain.value_objects.attachment import MessageAttachment

class AiConversation:
    def __init__(self, user_id: str, conversation_id: Optional[str] = None, title: Optional[str] = None, 
                 messages: List[AiMessage] = None, created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        self.id = conversation_id or str(uuid.uuid4())
        self.user_id = user_id
        self.title = title
        self.messages = messages or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def add_message(self, role: str, content: str, attachments: List[MessageAttachment] = None) -> AiMessage:
        message = AiMessage(role=role, content=content, attachments=attachments)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message
    
    def get_history_for_llm(self, limit: int = 10):
        # Return recent messages formatted for LLM context
        # This is a simplified version; real implementation might need token counting
        return self.messages[-limit:]
