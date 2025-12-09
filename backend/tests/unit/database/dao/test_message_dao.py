import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))
import json
from datetime import datetime, timedelta
from app_social.infrastructure.database.persistent_model.message_po import MessagePO
from app_social.infrastructure.database.dao_impl.sqlalchemy_message_dao import SqlAlchemyMessageDao

class TestMessageDao:
    
    @pytest.fixture
    def message_dao(self, db_session):
        return SqlAlchemyMessageDao(db_session)

    def test_find_by_conversation(self, message_dao, db_session):
        # m1: older
        m1 = MessagePO(
            id="m1", conversation_id="c1", sender_id="u1", 
            content_text="old", sent_at=datetime.utcnow() - timedelta(hours=1)
        )
        # m2: newer
        m2 = MessagePO(
            id="m2", conversation_id="c1", sender_id="u2", 
            content_text="new", sent_at=datetime.utcnow()
        )
        # m3: deleted
        m3 = MessagePO(
            id="m3", conversation_id="c1", sender_id="u1", 
            content_text="del", sent_at=datetime.utcnow(), is_deleted=True
        )
        # m4: other conv
        m4 = MessagePO(
            id="m4", conversation_id="c2", sender_id="u1", 
            content_text="other", sent_at=datetime.utcnow()
        )
        
        db_session.add_all([m1, m2, m3, m4])
        db_session.flush()
        
        msgs = message_dao.find_by_conversation("c1")
        assert len(msgs) == 2
        assert msgs[0].id == "m1" # Ordered by sent_at asc
        assert msgs[1].id == "m2"

    def test_mark_read(self, message_dao, db_session):
        m = MessagePO(
            id="m_read", conversation_id="c", sender_id="u1", 
            content_text="txt", read_by_json=json.dumps(["u1"])
        )
        message_dao.add(m)
        
        message_dao.mark_read("m_read", "u2")
        
        db_session.refresh(m)
        read_by = set(json.loads(m.read_by_json))
        assert "u2" in read_by
        assert "u1" in read_by

    def test_mark_all_read(self, message_dao, db_session):
        # m1: unread by u2
        m1 = MessagePO(id="m1", conversation_id="c1", sender_id="u1", content_text="txt", read_by_json='["u1"]')
        # m2: already read by u2
        m2 = MessagePO(id="m2", conversation_id="c1", sender_id="u1", content_text="txt", read_by_json='["u1", "u2"]')
        # m3: sent by u2 (should be ignored)
        m3 = MessagePO(id="m3", conversation_id="c1", sender_id="u2", content_text="txt", read_by_json='["u2"]')
        
        db_session.add_all([m1, m2, m3])
        db_session.flush()
        
        count = message_dao.mark_all_read("c1", "u2")
        
        assert count == 1 # Only m1 needed update
        
        db_session.refresh(m1)
        assert "u2" in json.loads(m1.read_by_json)

    def test_delete_logical(self, message_dao, db_session):
        m = MessagePO(id="m_del", conversation_id="c", sender_id="u", content_text="hi", is_deleted=False)
        message_dao.add(m)
        
        message_dao.delete("m_del")
        
        db_session.refresh(m)
        assert m.is_deleted is True
        
        # Should not be found in standard query
        msgs = message_dao.find_by_conversation("c")
        assert len(msgs) == 0

    def test_delete_by_conversation(self, message_dao, db_session):
        m1 = MessagePO(id="m1", conversation_id="c_del", sender_id="u", content_text="1")
        m2 = MessagePO(id="m2", conversation_id="c_del", sender_id="u", content_text="2")
        message_dao.add(m1)
        message_dao.add(m2)
        
        message_dao.delete_by_conversation("c_del")
        
        assert message_dao.find_by_id("m1") is None
        assert message_dao.find_by_id("m2") is None
