from typing import List, Optional
from datetime import datetime
from app_ai.domain.value_objects.attachment import MessageAttachment

class AiMessage:
    def __init__(self, role: str, content: str, attachments: List[MessageAttachment] = None, timestamp: Optional[datetime] = None):
        self.role = role
        self.content = content
        self.attachments = attachments or []
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "attachments": [att.to_dict() for att in self.attachments],
            "timestamp": self.timestamp.isoformat()
        }
