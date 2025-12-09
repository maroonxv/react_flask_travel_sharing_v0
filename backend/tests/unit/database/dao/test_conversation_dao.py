import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))
from datetime import datetime, timedelta
import json
from sqlalchemy import insert

from app_social.infrastructure.database.persistent_model.conversation_po import ConversationPO, conversation_participants
from app_social.infrastructure.database.persistent_model.message_po import MessagePO
from app_social.infrastructure.database.dao_impl.sqlalchemy_conversation_dao import SqlAlchemyConversationDao

class TestConversationDao:
    
    @pytest.fixture
    def conversation_dao(self, db_session):
        return SqlAlchemyConversationDao(db_session)

    def _add_participant(self, db_session, conversation_id, user_id):
        stmt = insert(conversation_participants).values(conversation_id=conversation_id, user_id=user_id)
        db_session.execute(stmt)
        db_session.flush()

    def test_find_by_participants_private(self, conversation_dao, db_session):
        # Arrange
        c1 = ConversationPO(id="c1", conversation_type="private", created_at=datetime.utcnow())
        conversation_dao.add(c1)
        self._add_participant(db_session, "c1", "u1")
        self._add_participant(db_session, "c1", "u2")
        
        # Noise: another conversation
        c2 = ConversationPO(id="c2", conversation_type="group", created_at=datetime.utcnow())
        conversation_dao.add(c2)
        self._add_participant(db_session, "c2", "u1")
        self._add_participant(db_session, "c2", "u2")

        # Act
        found = conversation_dao.find_by_participants("u1", "u2")
        
        # Assert
        assert found is not None
        assert found.id == "c1"
        assert found.conversation_type == "private"

    def test_find_by_user(self, conversation_dao, db_session):
        # c1: recent
        c1 = ConversationPO(id="c1", last_message_at=datetime.utcnow(), conversation_type="private")
        conversation_dao.add(c1)
        self._add_participant(db_session, "c1", "u_me")
        
        # c2: old
        c2 = ConversationPO(id="c2", last_message_at=datetime.utcnow() - timedelta(days=1), conversation_type="private")
        conversation_dao.add(c2)
        self._add_participant(db_session, "c2", "u_me")
        
        # c3: not mine
        c3 = ConversationPO(id="c3", last_message_at=datetime.utcnow(), conversation_type="private")
        conversation_dao.add(c3)
        self._add_participant(db_session, "c3", "u_other")

        results = conversation_dao.find_by_user("u_me")
        assert len(results) == 2
        assert results[0].id == "c1"  # Ordered by last_message_at desc
        assert results[1].id == "c2"

    def test_find_by_user_with_unread(self, conversation_dao, db_session):
        # Case 1: Unread message for me
        c1 = ConversationPO(id="c1", last_message_at=datetime.utcnow())
        conversation_dao.add(c1)
        self._add_participant(db_session, "c1", "me")
        
        msg1 = MessagePO(
            id="m1", conversation_id="c1", sender_id="other", 
            content_text="hi", is_deleted=False, 
            read_by_json=json.dumps(["other"]) # I haven't read it
        )
        db_session.add(msg1)
        
        # Case 2: I sent the message (should not count as unread for me)
        c2 = ConversationPO(id="c2", last_message_at=datetime.utcnow())
        conversation_dao.add(c2)
        self._add_participant(db_session, "c2", "me")
        
        msg2 = MessagePO(
            id="m2", conversation_id="c2", sender_id="me", 
            content_text="hello", is_deleted=False,
            read_by_json=json.dumps(["me"])
        )
        db_session.add(msg2)
        
        # Case 3: I read the message
        c3 = ConversationPO(id="c3", last_message_at=datetime.utcnow())
        conversation_dao.add(c3)
        self._add_participant(db_session, "c3", "me")
        
        msg3 = MessagePO(
            id="m3", conversation_id="c3", sender_id="other", 
            content_text="read", is_deleted=False,
            read_by_json=json.dumps(["other", "me"])
        )
        db_session.add(msg3)
        
        db_session.flush()

        # Act
        unread_convs = conversation_dao.find_by_user_with_unread("me")
        
        # Assert
        assert len(unread_convs) == 1
        assert unread_convs[0].id == "c1"

    def test_crud_operations(self, conversation_dao, db_session):
        c = ConversationPO(id="new", title="Initial", conversation_type="group")
        conversation_dao.add(c)
        
        found = conversation_dao.find_by_id("new")
        assert found.title == "Initial"
        
        c.title = "Updated"
        conversation_dao.update(c)
        db_session.refresh(c)
        assert conversation_dao.find_by_id("new").title == "Updated"
        
        assert conversation_dao.exists("new") is True
        
        conversation_dao.delete("new")
        assert conversation_dao.find_by_id("new") is None
