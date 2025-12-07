import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from app_social.infrastructure.database.repository_impl.conversation_repository_impl import ConversationRepositoryImpl
from app_social.domain.aggregate.conversation_aggregate import Conversation
from app_social.domain.entity.message_entity import Message
from app_social.domain.value_objects.social_value_objects import ConversationId, ConversationType, MessageContent
from app_social.infrastructure.database.persistent_model.conversation_po import ConversationPO
from app_social.infrastructure.database.persistent_model.message_po import MessagePO

class TestConversationRepository:
    
    @pytest.fixture
    def mock_conv_dao(self):
        return Mock()
    
    @pytest.fixture
    def mock_msg_dao(self):
        return Mock()
    
    @pytest.fixture
    def repo(self, mock_conv_dao, mock_msg_dao):
        return ConversationRepositoryImpl(mock_conv_dao, mock_msg_dao)

    @pytest.fixture
    def conversation(self):
        return Conversation.create_private("u1", "u2")

    def test_save_new_conversation(self, repo, mock_conv_dao, mock_msg_dao, conversation):
        # Setup
        mock_conv_dao.find_by_id.return_value = None
        mock_msg_dao.find_by_id.return_value = None
        
        # Action
        repo.save(conversation)
        
        # Verify
        mock_conv_dao.add.assert_called_once()
        args, _ = mock_conv_dao.add.call_args
        assert isinstance(args[0], ConversationPO)
        assert args[0].id == conversation.id.value
        
        mock_conv_dao.update_participants.assert_called_once()
        
    def test_save_existing_conversation(self, repo, mock_conv_dao, mock_msg_dao, conversation):
        # Setup
        existing_po = Mock(spec=ConversationPO)
        mock_conv_dao.find_by_id.return_value = existing_po
        mock_msg_dao.find_by_id.return_value = None
        
        # Action
        repo.save(conversation)
        
        # Verify
        existing_po.update_from_domain.assert_called_once_with(conversation)
        mock_conv_dao.update.assert_called_once_with(existing_po)

    def test_save_messages(self, repo, mock_conv_dao, mock_msg_dao, conversation):
        # Setup
        msg = conversation.send_message("u1", MessageContent("Hello"))
        mock_conv_dao.find_by_id.return_value = Mock(spec=ConversationPO) # Existing conv
        
        # Case 1: New message
        mock_msg_dao.find_by_id.return_value = None
        repo.save(conversation)
        mock_msg_dao.add.assert_called_once()
        
        # Case 2: Existing message (update)
        mock_msg_dao.reset_mock()
        existing_msg_po = Mock(spec=MessagePO)
        mock_msg_dao.find_by_id.return_value = existing_msg_po
        
        repo.save(conversation)
        existing_msg_po.update_from_domain.assert_called_once_with(msg)
        mock_msg_dao.update.assert_called_once_with(existing_msg_po)

    def test_find_by_id_found(self, repo, mock_conv_dao, mock_msg_dao):
        # Setup
        conv_id = "c1"
        conv_po = Mock(spec=ConversationPO)
        conv_po.id = conv_id
        
        # Create a real domain object to return from to_domain
        # Conversation requires at least 2 participants
        expected_domain = Conversation.reconstitute(ConversationId(conv_id), {"u1", "u2"}, [], ConversationType.PRIVATE)
        conv_po.to_domain.return_value = expected_domain
        
        mock_conv_dao.find_by_id.return_value = conv_po
        mock_msg_dao.find_by_conversation.return_value = []
        mock_conv_dao.get_participant_ids.return_value = ["u1", "u2"]
        
        # Action
        result = repo.find_by_id(ConversationId(conv_id))
        
        # Verify
        assert result == expected_domain
        mock_conv_dao.find_by_id.assert_called_with(conv_id)
        mock_msg_dao.find_by_conversation.assert_called_with(conv_id)
        conv_po.to_domain.assert_called_once()

    def test_find_by_id_not_found(self, repo, mock_conv_dao):
        mock_conv_dao.find_by_id.return_value = None
        result = repo.find_by_id(ConversationId("c1"))
        assert result is None

    def test_find_by_participants(self, repo, mock_conv_dao, mock_msg_dao):
        conv_po = Mock(spec=ConversationPO)
        conv_po.id = "c1"
        mock_conv_dao.find_by_participants.return_value = conv_po
        mock_msg_dao.find_by_conversation.return_value = []
        
        expected_domain = Mock(spec=Conversation)
        conv_po.to_domain.return_value = expected_domain
        
        result = repo.find_by_participants("u1", "u2")
        assert result == expected_domain
        mock_conv_dao.find_by_participants.assert_called_with("u1", "u2")

    def test_find_by_user(self, repo, mock_conv_dao, mock_msg_dao):
        conv_po = Mock(spec=ConversationPO)
        conv_po.id = "c1"
        mock_conv_dao.find_by_user.return_value = [conv_po]
        mock_msg_dao.find_by_conversation.return_value = []
        mock_conv_dao.get_participant_ids.return_value = ["u1"]
        
        result = repo.find_by_user("u1")
        assert len(result) == 1
        conv_po.to_domain.assert_called_once()

    def test_find_by_user_with_unread(self, repo, mock_conv_dao, mock_msg_dao):
        conv_po = Mock(spec=ConversationPO)
        conv_po.id = "c1"
        mock_conv_dao.find_by_user_with_unread.return_value = [conv_po]
        mock_msg_dao.find_by_conversation.return_value = []
        mock_conv_dao.get_participant_ids.return_value = ["u1"]
        
        result = repo.find_by_user_with_unread("u1")
        assert len(result) == 1

    def test_delete(self, repo, mock_conv_dao, mock_msg_dao):
        c_id = ConversationId("c1")
        repo.delete(c_id)
        
        mock_msg_dao.delete_by_conversation.assert_called_with("c1")
        mock_conv_dao.delete.assert_called_with("c1")

    def test_exists(self, repo, mock_conv_dao):
        mock_conv_dao.exists.return_value = True
        assert repo.exists(ConversationId("c1")) is True
