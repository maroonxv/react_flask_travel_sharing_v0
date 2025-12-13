
import pytest
import json
from datetime import datetime, date, time
from unittest.mock import MagicMock, patch
from app import create_app
from shared.database.core import SessionLocal, Base, engine
from app_auth.infrastructure.database.persistent_model.user_po import UserPO
from app_travel.infrastructure.database.persistent_model.trip_po import ActivityPO, TripPO, TripDayPO
from app_social.infrastructure.database.persistent_model.post_po import PostPO
from app_ai.infrastructure.database.persistent_model.ai_po import AiConversationPO, AiMessagePO

@pytest.fixture(scope='module')
def test_app():
    app = create_app()
    app.config['TESTING'] = True
    yield app

@pytest.fixture(scope='module')
def client(test_app):
    return test_app.test_client()

@pytest.fixture(scope='function')
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope='function')
def test_user(db):
    user = UserPO(
        id='test_user_id',
        username='test_user',
        email='test@example.com',
        hashed_password='hashed_password'
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture(scope='function')
def test_data(db):
    # Create Trip
    trip = TripPO(
        id='trip_1',
        name='Beijing Trip',
        creator_id='test_user_id',
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 3),
        visibility='public',
        status='planning'
    )
    db.add(trip)
    
    # Create TripDay
    trip_day = TripDayPO(
        id=1,
        trip_id='trip_1',
        day_number=1,
        date=date(2023, 1, 1)
    )
    db.add(trip_day)
    
    # Add an activity
    activity = ActivityPO(
        id='act_1',
        trip_day_id=1,
        name='The Great Wall',
        activity_type='sightseeing',
        location_name='Beijing',
        start_time=time(9, 0),
        end_time=time(12, 0)
    )
    
    # Add a post
    post = PostPO(
        id='post_1',
        author_id='test_user_id',
        title='My trip to Beijing',
        text='Beijing is amazing! The food is great.',
        visibility='public'
    )
    db.add(activity)
    db.add(post)
    db.commit()

class MockLlmStream:
    def __iter__(self):
        yield type('Chunk', (), {'content': 'Hello '})()
        yield type('Chunk', (), {'content': 'Beijing!'})()

@patch('app_ai.infrastructure.llm.langchain_deepseek_adapter.LangChainDeepSeekAdapter.stream_chat')
def test_chat_flow(mock_stream_chat, client, db, test_user, test_data):
    # Setup Mock LLM Response
    mock_stream_chat.return_value = ["Hello ", "Beijing!"]
    
    # 1. Start a new chat
    payload = {
        "user_id": test_user.id,
        "message": "Beijing"
    }
    
    response = client.post('/api/ai/chat', json=payload)
    assert response.status_code == 200
    assert response.mimetype == 'text/event-stream'
    
    # Consume the stream by reading data
    # response.data will consume the generator
    full_content = response.data.decode('utf-8')
    
    events = []
    # Split by double newline which separates events in SSE
    raw_events = full_content.split('\n\n')
    
    for raw_event in raw_events:
        if not raw_event.strip():
            continue
        
        event_name = None
        event_data = None
        
        for line in raw_event.split('\n'):
            if line.startswith('event:'):
                event_name = line.split(': ', 1)[1]
            elif line.startswith('data:'):
                try:
                    event_data = json.loads(line.split(': ', 1)[1])
                except json.JSONDecodeError:
                    pass
        
        if event_name and event_data:
            events.append((event_name, event_data))
            
    # Verify events
    event_types = [e[0] for e in events]
    assert 'init' in event_types
    assert 'text_chunk' in event_types
    assert 'message_end' in event_types
    # Verify attachment is present (since we added data about Beijing)
    assert 'attachment' in event_types
    
    # Verify DB persistence
    # Get conversation ID from init event
    conv_id = next(e[1]['conversation_id'] for e in events if e[0] == 'init')
    
    # Check DB
    conv = db.query(AiConversationPO).filter_by(id=conv_id).first()
    assert conv is not None
    assert len(conv.messages) == 2 # User + Assistant
    assert conv.messages[0].role == 'user'
    assert conv.messages[0].content == "Beijing"
    assert conv.messages[1].role == 'assistant'
    assert conv.messages[1].content == "Hello Beijing!"

@patch('app_ai.infrastructure.llm.langchain_deepseek_adapter.LangChainDeepSeekAdapter.stream_chat')
def test_chat_with_history(mock_stream_chat, client, db, test_user):
    # Setup existing conversation
    conv = AiConversationPO(id='existing_conv', user_id=test_user.id, title='Old Chat')
    msg = AiMessagePO(conversation_id='existing_conv', role='user', content='Hi')
    db.add(conv)
    db.add(msg)
    db.commit()
    
    mock_stream_chat.return_value = ["Sure."]
    
    payload = {
        "user_id": test_user.id,
        "conversation_id": "existing_conv",
        "message": "Continue"
    }
    
    response = client.post('/api/ai/chat', json=payload)
    assert response.status_code == 200
    
    # Force consumption of the stream to trigger DB save
    _ = response.data
    
    # Verify DB has new messages
    db.expire_all()
    conv = db.query(AiConversationPO).filter_by(id='existing_conv').first()
    # Old: 1 msg. New: +1 user + 1 AI = 3 total.
    assert len(conv.messages) == 3 
