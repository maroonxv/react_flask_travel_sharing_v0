import pytest
from app_social.domain.value_objects.social_value_objects import MessageContent
from app_social.domain.aggregate.conversation_aggregate import Conversation
from app_social.domain.domain_event.social_events import MessageSentEvent

def test_message_content_cleanliness():
    """
    Test that the message content in MessageSentEvent matches exactly what was input,
    without any appended timestamps or extra data.
    """
    # Arrange
    user1 = "u1"
    user2 = "u2"
    conv = Conversation.create_private(user1, user2)
    original_text = "test message"
    content = MessageContent(text=original_text)
    
    # Act
    message = conv.send_message(user1, content)
    
    # Assert
    # 1. Check message entity
    assert message.content.text == original_text
    
    # 2. Check emitted event
    # We need to capture the event from conv._domain_events (which is protected/private in Python convention but accessible)
    # However, Conversation.pop_events() or similar might be used. 
    # Let's inspect _domain_events directly for unit testing.
    # The aggregate has `_domain_events` list.
    
    events = conv._domain_events
    message_events = [e for e in events if isinstance(e, MessageSentEvent)]
    
    assert len(message_events) > 0
    event = message_events[0]
    
    assert event.content == original_text
    assert "13:24" not in event.content

