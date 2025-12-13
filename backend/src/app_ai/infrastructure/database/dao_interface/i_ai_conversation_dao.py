from abc import ABC, abstractmethod
from typing import Optional, List
from app_ai.infrastructure.database.persistent_model.ai_po import AiConversationPO

class IAiConversationDao(ABC):
    @abstractmethod
    def save(self, po: AiConversationPO) -> None:
        pass
        
    @abstractmethod
    def get_by_id(self, conversation_id: str) -> Optional[AiConversationPO]:
        pass
        
    @abstractmethod
    def get_by_user_id(self, user_id: str, limit: int = 20) -> List[AiConversationPO]:
        pass
