from typing import List, Optional
from sqlalchemy.orm import Session
from app_ai.infrastructure.database.persistent_model.ai_po import AiConversationPO
from app_ai.infrastructure.database.dao_interface.i_ai_conversation_dao import IAiConversationDao

class SqlAlchemyAiConversationDao(IAiConversationDao):
    def __init__(self, session: Session):
        self.session = session
        
    def save(self, po: AiConversationPO) -> None:
        self.session.merge(po)
        self.session.flush()
        
    def get_by_id(self, conversation_id: str) -> Optional[AiConversationPO]:
        return self.session.query(AiConversationPO).filter(
            AiConversationPO.id == conversation_id,
            AiConversationPO.is_deleted == False
        ).first()
        
    def get_by_user_id(self, user_id: str, limit: int = 20) -> List[AiConversationPO]:
        return self.session.query(AiConversationPO).filter(
            AiConversationPO.user_id == user_id,
            AiConversationPO.is_deleted == False
        ).order_by(AiConversationPO.updated_at.desc()).limit(limit).all()
