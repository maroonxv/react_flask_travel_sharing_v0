import json
from typing import List, Optional
from app_ai.domain.aggregate.ai_conversation import AiConversation
from app_ai.domain.entity.ai_message import AiMessage
from app_ai.domain.value_objects.attachment import MessageAttachment
from app_ai.domain.demand_interface.i_ai_repository import IAiRepository
from app_ai.infrastructure.database.dao_interface.i_ai_conversation_dao import IAiConversationDao
from app_ai.infrastructure.database.persistent_model.ai_po import AiConversationPO, AiMessagePO

class AiRepositoryImpl(IAiRepository):
    def __init__(self, conversation_dao: IAiConversationDao):
        self.conversation_dao = conversation_dao
        
    def save(self, conversation: AiConversation) -> None:
        po = self._to_po(conversation)
        self.conversation_dao.save(po)
        
    def get_by_id(self, conversation_id: str) -> Optional[AiConversation]:
        po = self.conversation_dao.get_by_id(conversation_id)
        if not po:
            return None
        return self._to_domain(po)
        
    def get_by_user_id(self, user_id: str, limit: int = 20) -> List[AiConversation]:
        pos = self.conversation_dao.get_by_user_id(user_id, limit)
        return [self._to_domain(po) for po in pos]
        
    def _to_po(self, conversation: AiConversation) -> AiConversationPO:
        messages_po = []
        for msg in conversation.messages:
            msg_po = AiMessagePO(
                conversation_id=conversation.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.timestamp,
                attachments_json=json.dumps([att.to_dict() for att in msg.attachments]) if msg.attachments else None
            )
            messages_po.append(msg_po)
            
        return AiConversationPO(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages_po
        )
        
    def _to_domain(self, po: AiConversationPO) -> AiConversation:
        domain_messages = []
        for msg_po in po.messages:
            attachments = []
            if msg_po.attachments_json:
                try:
                    att_list = json.loads(msg_po.attachments_json)
                    attachments = [MessageAttachment.from_dict(att) for att in att_list]
                except json.JSONDecodeError:
                    pass
            
            domain_msg = AiMessage(
                role=msg_po.role,
                content=msg_po.content,
                attachments=attachments,
                timestamp=msg_po.created_at
            )
            domain_messages.append(domain_msg)
            
        return AiConversation(
            user_id=po.user_id,
            conversation_id=po.id,
            title=po.title,
            messages=domain_messages,
            created_at=po.created_at,
            updated_at=po.updated_at
        )
