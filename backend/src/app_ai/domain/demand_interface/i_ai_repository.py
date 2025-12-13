from abc import ABC, abstractmethod
from typing import Optional, List
from app_ai.domain.aggregate.ai_conversation import AiConversation

class IAiRepository(ABC):
    @abstractmethod
    def save(self, conversation: AiConversation) -> None:
        """保存或更新整个聚合根"""
        pass

    @abstractmethod
    def get_by_id(self, conversation_id: str) -> Optional[AiConversation]:
        """根据ID获取聚合根"""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: str, limit: int = 20) -> List[AiConversation]:
        """获取用户的会话列表"""
        pass
