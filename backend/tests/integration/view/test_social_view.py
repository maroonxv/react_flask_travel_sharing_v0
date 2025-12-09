import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import json
import uuid
from flask import Flask, g
from unittest.mock import patch, MagicMock

from app_social.view.social_view import social_bp
from app_social.services.social_service import SocialService

# ==================== Fixtures ====================

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(social_bp)
    
    # Register error handlers if needed, or simple teardown
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user_id():
    return str(uuid.uuid4())

@pytest.fixture
def auth_header(user_id):
    return {'X-User-Id': user_id}

# We need to mock SessionLocal in SocialService to use our db_session
# But SocialService is instantiated at module level in social_view.py!
# This is tricky. When social_view is imported, SocialService() is called.
# To mock it effectively for integration tests that use the real service logic but test DB,
# we need to patch SessionLocal inside social_service.py BEFORE it's used by the view's service instance.
# Actually, the view imports `social_service` instance.
# If we patch `app_social.services.social_service.SessionLocal`, it will affect the instance's methods.

@pytest.fixture
def mock_db_session(db_session):
    with patch('app_social.services.social_service.SessionLocal', return_value=db_session):
        yield db_session

# ==================== Tests ====================

class TestSocialViewIntegration:
    
    def test_create_post(self, client, auth_header, mock_db_session):
        data = {
            "title": "API Post",
            "content": "Content from API",
            "tags": ["api", "test"],
            "visibility": "public"
        }
        
        response = client.post('/api/social/posts', json=data, headers=auth_header)
        
        assert response.status_code == 201
        res_json = response.get_json()
        assert "post_id" in res_json
        assert "created_at" in res_json

    def test_create_post_unauthorized(self, client):
        data = {"title": "No Auth"}
        response = client.post('/api/social/posts', json=data) # No headers
        assert response.status_code == 400 or response.status_code == 500
        # In _get_current_user_id, it raises ValueError("Unauthorized")
        # _handle_error catches it and returns 400.
        assert response.status_code == 400
        assert "Unauthorized" in response.get_json()["error"]

    def test_get_post(self, client, auth_header, mock_db_session):
        # First create one
        create_res = client.post('/api/social/posts', json={"title": "Get Me", "content": "C"}, headers=auth_header)
        post_id = create_res.get_json()["post_id"]
        
        # Clear identity map to ensure fresh read
        mock_db_session.expire_all()
        
        response = client.get(f'/api/social/posts/{post_id}', headers=auth_header)
        assert response.status_code == 200
        res_json = response.get_json()
        assert res_json["title"] == "Get Me"
        assert res_json["id"] == post_id

    def test_get_post_not_found(self, client, auth_header, mock_db_session):
        response = client.get(f'/api/social/posts/{uuid.uuid4()}', headers=auth_header)
        assert response.status_code == 404

    def test_update_post(self, client, auth_header, mock_db_session):
        create_res = client.post('/api/social/posts', json={"title": "Old", "content": "Old"}, headers=auth_header)
        post_id = create_res.get_json()["post_id"]
        
        update_data = {"title": "New", "content": "New"}
        response = client.put(f'/api/social/posts/{post_id}', json=update_data, headers=auth_header)
        
        assert response.status_code == 200
        
        # Verify
        get_res = client.get(f'/api/social/posts/{post_id}', headers=auth_header)
        assert get_res.get_json()["title"] == "New"

    def test_delete_post(self, client, auth_header, mock_db_session):
        create_res = client.post('/api/social/posts', json={"title": "Del", "content": "Content"}, headers=auth_header)
        post_id = create_res.get_json()["post_id"]
        
        response = client.delete(f'/api/social/posts/{post_id}', headers=auth_header)
        assert response.status_code == 200
        
        # Verify it's gone (or at least not found/accessible)
        get_res = client.get(f'/api/social/posts/{post_id}', headers=auth_header)
        # get_post_detail checks permission, deleted post -> can_be_viewed_by returns False -> Permission denied (ValueError)
        # _handle_error maps ValueError to 400
        assert get_res.status_code == 400
        assert "Permission denied" in get_res.get_json()["error"]

    def test_like_post(self, client, auth_header, mock_db_session):
        create_res = client.post('/api/social/posts', json={"title": "Like", "content": "Content"}, headers=auth_header)
        post_id = create_res.get_json()["post_id"]
        
        # Like
        res1 = client.post(f'/api/social/posts/{post_id}/like', headers=auth_header)
        assert res1.status_code == 200
        assert res1.get_json()["is_liked"] is True
        
        # Unlike
        res2 = client.post(f'/api/social/posts/{post_id}/like', headers=auth_header)
        assert res2.status_code == 200
        assert res2.get_json()["is_liked"] is False

    def test_add_comment(self, client, auth_header, mock_db_session):
        create_res = client.post('/api/social/posts', json={"title": "Comment", "content": "Content"}, headers=auth_header)
        post_id = create_res.get_json()["post_id"]
        
        res = client.post(f'/api/social/posts/{post_id}/comments', json={"content": "Nice"}, headers=auth_header)
        assert res.status_code == 201
        assert "comment_id" in res.get_json()

    def test_feed(self, client, auth_header, mock_db_session):
        client.post('/api/social/posts', json={"title": "P1", "content": "C1", "tags": ["A"], "visibility": "public"}, headers=auth_header)
        client.post('/api/social/posts', json={"title": "P2", "content": "C2", "tags": ["B"], "visibility": "public"}, headers=auth_header)
        
        # Filter by tag A
        res = client.get('/api/social/feed?tags=A', headers=auth_header)
        assert res.status_code == 200
        items = res.get_json()
        titles = [i["title"] for i in items]
        assert "P1" in titles
        assert "P2" not in titles

    def test_user_posts(self, client, auth_header, mock_db_session, user_id):
        client.post('/api/social/posts', json={"title": "My P1", "content": "C1"}, headers=auth_header)
        
        res = client.get(f'/api/social/users/{user_id}/posts', headers=auth_header)
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_create_conversation(self, client, auth_header, mock_db_session):
        other_id = str(uuid.uuid4())
        res = client.post('/api/social/conversations', json={"target_id": other_id}, headers=auth_header)
        assert res.status_code == 201
        assert "conversation_id" in res.get_json()

    def test_send_and_get_messages(self, client, auth_header, mock_db_session):
        # Create conv
        other_id = str(uuid.uuid4())
        conv_res = client.post('/api/social/conversations', json={"target_id": other_id}, headers=auth_header)
        conv_id = conv_res.get_json()["conversation_id"]
        
        # Send msg
        msg_res = client.post(f'/api/social/conversations/{conv_id}/messages', json={"content": "Hi"}, headers=auth_header)
        assert msg_res.status_code == 201
        
        # Get msgs
        get_res = client.get(f'/api/social/conversations/{conv_id}/messages', headers=auth_header)
        assert get_res.status_code == 200
        msgs = get_res.get_json()
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Hi"

    def test_get_conversations_list(self, client, auth_header, mock_db_session):
        other_id = str(uuid.uuid4())
        client.post('/api/social/conversations', json={"target_id": other_id}, headers=auth_header)
        
        res = client.get('/api/social/conversations', headers=auth_header)
        assert res.status_code == 200
        assert len(res.get_json()) >= 1
