import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import uuid
from datetime import datetime
from app_social.domain.aggregate.conversation_aggregate import Conversation
from app_social.domain.entity.message_entity import Message
from app_social.domain.value_objects.social_value_objects import ConversationId, ConversationType, MessageContent
from app_social.infrastructure.database.dao_impl.sqlalchemy_conversation_dao import SqlAlchemyConversationDao
from app_social.infrastructure.database.dao_impl.sqlalchemy_message_dao import SqlAlchemyMessageDao
from app_social.infrastructure.database.repository_impl.conversation_repository_impl import ConversationRepositoryImpl

class TestConversationRepositoryIntegration:
    
    @pytest.fixture
    def conv_repo(self, integration_db_session):
        c_dao = SqlAlchemyConversationDao(integration_db_session)
        m_dao = SqlAlchemyMessageDao(integration_db_session)
        return ConversationRepositoryImpl(c_dao, m_dao)

    def test_save_conversation_with_messages(self, conv_repo):
        # Arrange
        u1 = "user_integration_1"
        u2 = "user_integration_2"
        
        # Use factory method which is safer and cleaner
        conv = Conversation.create_private(initiator_id=u1, participant_id=u2)
        
        # Add message from one of the participants
        conv.send_message(
            sender_id=u1,
            content=MessageContent(text="Integration Hello")
        )

        # Act
        # Note: Repository implementation handles saving both conversation and messages
        
        conv_repo.save(conv)

        # Assert
        found = conv_repo.find_by_id(conv.id)
        assert found is not None
        assert len(found.messages) == 1
        assert found.messages[0].content.text == "Integration Hello"

    def test_find_by_participants_integration(self, conv_repo, integration_db_session):
        # Repo now saves participants, so we can test normally
        
        cid = str(uuid.uuid4())
        u1 = "user_A"
        u2 = "user_B"
        
        # 1. Create Conv via Repo
        conv = Conversation.reconstitute(
            conversation_id=ConversationId(cid),
            participant_ids={u1, u2},
            messages=[],
            conversation_type=ConversationType.PRIVATE,
            created_at=datetime.utcnow()
        )
        conv_repo.save(conv)
        
        # Act
        found = conv_repo.find_by_participants(u1, u2)
        
        # Assert
        assert found is not None
        assert found.id.value == cid
