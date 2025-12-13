import json
from typing import Generator
from app_ai.domain.demand_interface.i_ai_repository import IAiRepository
from app_ai.domain.domain_service.ai_chat_domain_service import AiChatDomainService
from app_ai.domain.aggregate.ai_conversation import AiConversation
from app_ai.domain.value_objects.attachment import MessageAttachment

class AiApplicationService:
    def __init__(self, repository: IAiRepository, domain_service: AiChatDomainService):
        self.repository = repository
        self.domain_service = domain_service

    def get_user_conversations(self, user_id: str):
        return self.repository.get_by_user_id(user_id)

    def get_conversation_detail(self, conversation_id: str, user_id: str):
        conversation = self.repository.get_by_id(conversation_id)
        if not conversation or conversation.user_id != user_id:
            return None
        return conversation

    def create_conversation(self, user_id: str, title: str = "New Chat"):
        conversation = AiConversation(user_id=user_id, title=title)
        self.repository.save(conversation)
        return conversation

    def chat_stream(self, user_id: str, query: str, conversation_id: str = None) -> Generator[str, None, None]:
        # 1. Load or Create Conversation
        if conversation_id:
            conversation = self.repository.get_by_id(conversation_id)
            if not conversation or conversation.user_id != user_id:
                yield f"data: {json.dumps({'error': 'Conversation not found'})}\n\n"
                return
        else:
            conversation = AiConversation(user_id=user_id, title=query[:20])
            self.repository.save(conversation)
            # Send the new conversation ID to client first
            yield f"event: init\ndata: {json.dumps({'conversation_id': conversation.id})}\n\n"

        # 2. Add User Message (Persist first)
        conversation.add_message(role="user", content=query)
        self.repository.save(conversation) # Save user message
        
        # 3. Stream from Domain Service
        full_text = ""
        attachments_data = []
        
        for event in self.domain_service.stream_response(conversation, query):
            if event["event"] == "internal_complete":
                full_text = event["data"]["full_text"]
                attachments_data = event["data"]["attachments"]
            else:
                # Format as SSE
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
        
        # 4. Save AI Response to DB
        attachments = [MessageAttachment.from_dict(att) for att in attachments_data]
        conversation.add_message(role="assistant", content=full_text, attachments=attachments)
        self.repository.save(conversation)
