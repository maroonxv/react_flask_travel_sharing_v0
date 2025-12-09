import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
from datetime import datetime
import uuid

from app_social.domain.aggregate.conversation_aggregate import Conversation
from app_social.domain.value_objects.social_value_objects import (
    ConversationId, MessageContent, ConversationType
)
from app_social.domain.domain_event.social_events import (
    ConversationCreatedEvent, MessageSentEvent, MessageDeletedEvent,
    MessagesReadEvent, ParticipantAddedEvent, ParticipantRemovedEvent
)

class TestConversationAggregate:
    
    @pytest.fixture
    def user1(self):
        return "user_1"
    
    @pytest.fixture
    def user2(self):
        return "user_2"
    
    @pytest.fixture
    def user3(self):
        return "user_3"

    def test_create_private_conversation(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        
        assert conv.id is not None
        assert conv.conversation_type == ConversationType.PRIVATE
        assert conv.participant_count == 2
        assert conv.is_participant(user1)
        assert conv.is_participant(user2)
        assert not conv.is_group
        assert conv.title is None
        
        events = conv.pop_events()
        assert len(events) == 1
        assert isinstance(events[0], ConversationCreatedEvent)

    def test_create_private_self_error(self, user1):
        with pytest.raises(ValueError, match="Cannot create conversation with yourself"):
            Conversation.create_private(user1, user1)

    def test_create_group_conversation(self, user1, user2, user3):
        conv = Conversation.create_group(user1, [user2, user3], title="Group Chat")
        
        assert conv.is_group
        assert conv.participant_count == 3
        assert conv.title == "Group Chat"
        
        events = conv.pop_events()
        assert isinstance(events[0], ConversationCreatedEvent)

    def test_create_group_insufficient_participants(self, user1):
        with pytest.raises(ValueError, match="Group chat requires at least 2 participants"):
            Conversation.create_group(user1, []) # Only creator

    def test_reconstitute(self, user1, user2):
        conv_id = ConversationId.generate()
        conv = Conversation.reconstitute(
            conversation_id=conv_id,
            participant_ids={user1, user2},
            messages=[],
            conversation_type=ConversationType.PRIVATE
        )
        assert conv.id == conv_id
        assert conv.participant_count == 2

    def test_send_message(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        content = MessageContent(text="Hello")
        
        msg = conv.send_message(user1, content)
        
        assert len(conv.messages) == 1
        assert conv.message_count == 1
        assert conv.last_message_at == msg.sent_at
        assert msg.sender_id == user1
        assert msg.content.text == "Hello"
        
        events = conv.pop_events()
        # 0: created, 1: message sent
        assert isinstance(events[1], MessageSentEvent)

    def test_send_message_not_participant(self, user1, user2, user3):
        conv = Conversation.create_private(user1, user2)
        content = MessageContent(text="Hello")
        
        with pytest.raises(ValueError, match="Sender is not a participant"):
            conv.send_message(user3, content)

    def test_delete_message(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        msg = conv.send_message(user1, MessageContent(text="Hello"))
        
        conv.delete_message(msg.message_id, user1)
        
        assert len(conv.messages) == 0
        assert conv.message_count == 0
        
        events = conv.pop_events()
        assert isinstance(events[2], MessageDeletedEvent)

    def test_delete_message_permission(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        msg = conv.send_message(user1, MessageContent(text="Hello"))
        
        with pytest.raises(ValueError, match="Only sender can delete"):
            conv.delete_message(msg.message_id, user2)

    def test_delete_nonexistent_message(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        with pytest.raises(ValueError, match="Message not found"):
            conv.delete_message("fake_id", user1)

    def test_mark_as_read(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        msg1 = conv.send_message(user1, MessageContent(text="Hi"))
        msg2 = conv.send_message(user1, MessageContent(text="How are you"))
        
        assert conv.get_unread_count(user2) == 2
        
        count = conv.mark_as_read(user2)
        assert count == 2
        assert conv.get_unread_count(user2) == 0
        
        events = conv.pop_events()
        assert isinstance(events[-1], MessagesReadEvent)

    def test_mark_as_read_partial(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        msg1 = conv.send_message(user1, MessageContent(text="Hi"))
        msg2 = conv.send_message(user1, MessageContent(text="How are you"))
        
        count = conv.mark_as_read(user2, up_to_message_id=msg1.message_id)
        assert count == 1
        assert conv.get_unread_count(user2) == 1

    def test_mark_as_read_not_participant(self, user1, user2, user3):
        conv = Conversation.create_private(user1, user2)
        with pytest.raises(ValueError, match="User is not a participant"):
            conv.mark_as_read(user3)

    def test_add_participant(self, user1, user2, user3):
        conv = Conversation.create_group(user1, [user2], title="Group")
        
        conv.add_participant(user3, added_by=user1)
        assert conv.participant_count == 3
        assert conv.is_participant(user3)
        
        events = conv.pop_events()
        assert isinstance(events[1], ParticipantAddedEvent)

    def test_add_participant_private_error(self, user1, user2, user3):
        conv = Conversation.create_private(user1, user2)
        with pytest.raises(ValueError, match="Cannot add participants to private conversation"):
            conv.add_participant(user3, user1)

    def test_add_participant_permission(self, user1, user2, user3):
        conv = Conversation.create_group(user1, [user2])
        with pytest.raises(ValueError, match="Only participants can add"):
            conv.add_participant(user3, added_by="stranger")

    def test_remove_participant(self, user1, user2, user3):
        conv = Conversation.create_group(user1, [user2, user3])
        
        conv.remove_participant(user3, removed_by=user3) # Self remove
        assert conv.participant_count == 2
        assert not conv.is_participant(user3)
        
        events = conv.pop_events()
        assert isinstance(events[1], ParticipantRemovedEvent)

    def test_remove_participant_private_error(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        with pytest.raises(ValueError, match="Cannot remove participants from private conversation"):
            conv.remove_participant(user2, user2)

    def test_remove_participant_permission(self, user1, user2, user3):
        conv = Conversation.create_group(user1, [user2, user3])
        # Only allow self-remove for now
        with pytest.raises(ValueError, match="Can only remove yourself"):
            conv.remove_participant(user2, removed_by=user1)

    def test_remove_participant_min_limit(self, user1, user2):
        conv = Conversation.create_group(user1, [user2])
        with pytest.raises(ValueError, match="Cannot have less than 2 participants"):
            conv.remove_participant(user2, removed_by=user2)

    def test_update_title(self, user1, user2, user3):
        conv = Conversation.create_group(user1, [user2])
        conv.update_title("New Title", updated_by=user1)
        assert conv.title == "New Title"

    def test_update_title_private_error(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        with pytest.raises(ValueError, match="Cannot set title for private conversation"):
            conv.update_title("Title", user1)

    def test_get_other_participant(self, user1, user2):
        conv = Conversation.create_private(user1, user2)
        assert conv.get_other_participant(user1) == user2
        assert conv.get_other_participant(user2) == user1
        
        # Group chat returns None
        group = Conversation.create_group(user1, [user2])
        assert group.get_other_participant(user1) is None
