import pytest
import json
from unittest.mock import MagicMock, patch
from app import create_app
from shared.database.core import SessionLocal, Base, engine
from app_auth.infrastructure.database.persistent_model.user_po import UserPO
from app_ai.infrastructure.database.persistent_model.ai_po import AiConversationPO

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
    # Use real DB but with caution - though for view tests we mostly mock the service layer
    # Actually, if we mock get_ai_service, we don't need real DB connection for the View logic
    # But view might access g.session.
    # Let's mock the service injection in the View.
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope='function')
def mock_service():
    with patch('app_ai.view.ai_view.get_ai_service') as mock:
        yield mock

def test_chat_endpoint_success(client, mock_service):
    # Setup mock
    service_instance = MagicMock()
    mock_service.return_value = service_instance
    
    # Mock chat_stream generator
    def mock_generator(user_id, query, conversation_id):
        yield "event: init\ndata: {\"conversation_id\": \"123\"}\n\n"
        yield "event: text_chunk\ndata: {\"delta\": \"Hi\", \"finish\": false}\n\n"
        yield "event: message_end\ndata: {\"full_text\": \"Hi\"}\n\n"
        
    service_instance.chat_stream.side_effect = mock_generator
    
    # Make request
    response = client.post('/api/ai/chat', json={
        "user_id": "test_user",
        "message": "Hello"
    })
    
    assert response.status_code == 200
    assert response.mimetype == 'text/event-stream'
    
    content = response.data.decode('utf-8')
    assert "event: init" in content
    assert "event: text_chunk" in content

def test_chat_endpoint_missing_message(client):
    response = client.post('/api/ai/chat', json={
        "user_id": "test_user"
    })
    assert response.status_code == 400
    assert "Message is required" in response.json['error']

def test_chat_endpoint_unauthorized(client):
    # If we rely on user_id in body (temporary impl), missing it should be 401
    response = client.post('/api/ai/chat', json={
        "message": "Hello"
    })
    assert response.status_code == 401

def test_list_conversations(client, mock_service):
    service_instance = MagicMock()
    mock_service.return_value = service_instance
    
    # Mock data
    mock_conv = MagicMock()
    mock_conv.id = "c1"
    mock_conv.title = "Chat 1"
    mock_conv.updated_at.isoformat.return_value = "2023-01-01T12:00:00"
    
    service_instance.get_user_conversations.return_value = [mock_conv]
    
    response = client.get('/api/ai/conversations?user_id=test_user')
    
    assert response.status_code == 200
    data = response.json
    assert len(data) == 1
    assert data[0]['id'] == "c1"
    assert data[0]['title'] == "Chat 1"

def test_get_conversation_detail(client, mock_service):
    service_instance = MagicMock()
    mock_service.return_value = service_instance
    
    mock_conv = MagicMock()
    mock_conv.id = "c1"
    mock_conv.title = "Chat 1"
    
    mock_msg = MagicMock()
    mock_msg.to_dict.return_value = {"role": "user", "content": "hi"}
    mock_conv.messages = [mock_msg]
    
    service_instance.get_conversation_detail.return_value = mock_conv
    
    response = client.get('/api/ai/conversations/c1?user_id=test_user')
    
    assert response.status_code == 200
    data = response.json
    assert data['id'] == "c1"
    assert len(data['messages']) == 1

def test_get_conversation_not_found(client, mock_service):
    service_instance = MagicMock()
    mock_service.return_value = service_instance
    service_instance.get_conversation_detail.return_value = None
    
    response = client.get('/api/ai/conversations/c999?user_id=test_user')
    
    assert response.status_code == 404
