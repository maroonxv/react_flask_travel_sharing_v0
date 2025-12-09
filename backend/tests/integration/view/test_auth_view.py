import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import json
from flask import Flask, session
from unittest.mock import patch

from app_auth.view.auth_view import auth_bp
from app_auth.domain.domain_service.auth_service import AuthService as DomainAuthService

# ==================== Fixtures ====================

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'test_secret_key'
    app.register_blueprint(auth_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_db_session(db_session):
    """
    Patch SessionLocal in auth_view to return the test db_session.
    This ensures that the view uses the same session (and thus the same in-memory DB)
    as the test setup.
    """
    # auth_view imports SessionLocal from shared.database.core
    # But it uses it as g.session = SessionLocal()
    # So we patch the class/function in the auth_view module namespace
    with patch('app_auth.view.auth_view.SessionLocal', return_value=db_session):
        yield db_session

# ==================== Tests ====================

class TestAuthViewIntegration:
    
    def test_register_success(self, client, mock_db_session):
        data = {
            "username": "viewuser",
            "email": "view@test.com",
            "password": "password123",
            "role": "user"
        }
        
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 201
        res_json = response.get_json()
        assert res_json['username'] == "viewuser"
        assert res_json['email'] == "view@test.com"
        assert 'id' in res_json
        
        # Verify persistence (optional, but good for integration)
        # We can use SQL directly or just trust the response + login test

    def test_register_duplicate(self, client, mock_db_session):
        data = {
            "username": "dupuser",
            "email": "dup@test.com",
            "password": "password123"
        }
        # First registration
        client.post('/api/auth/register', json=data)
        
        # Second registration (same email)
        response = client.post('/api/auth/register', json=data)
        
        assert response.status_code == 400
        assert "already exists" in response.get_json()['error']

    def test_login_success(self, client, mock_db_session):
        # Register first
        register_data = {
            "username": "loginuser",
            "email": "login@test.com",
            "password": "password123"
        }
        client.post('/api/auth/register', json=register_data)
        
        # Login
        login_data = {
            "email": "login@test.com",
            "password": "password123"
        }
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 200
        res_json = response.get_json()
        assert res_json['username'] == "loginuser"
        
        # Verify session works by accessing protected route
        me_res = client.get('/api/auth/me')
        assert me_res.status_code == 200
        assert me_res.get_json()['username'] == "loginuser"

    def test_login_fail(self, client, mock_db_session):
        login_data = {
            "email": "nonexistent@test.com",
            "password": "password123"
        }
        response = client.post('/api/auth/login', json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.get_json()['error']

    def test_logout(self, client, mock_db_session):
        # Register & Login
        register_data = {"username": "logoutuser", "email": "logout@test.com", "password": "password123"}
        client.post('/api/auth/register', json=register_data)
        client.post('/api/auth/login', json={"email": "logout@test.com", "password": "password123"})
        
        # Logout
        response = client.post('/api/auth/logout')
        assert response.status_code == 200
        
        # Verify accessing protected route fails
        response = client.get('/api/auth/me')
        assert response.status_code == 401

    def test_get_current_user(self, client, mock_db_session):
        # Register & Login
        register_data = {"username": "meuser", "email": "me@test.com", "password": "password123"}
        client.post('/api/auth/register', json=register_data)
        client.post('/api/auth/login', json={"email": "me@test.com", "password": "password123"})
        
        # Get Me
        response = client.get('/api/auth/me')
        assert response.status_code == 200
        res_json = response.get_json()
        assert res_json['username'] == "meuser"

    def test_get_current_user_unauthorized(self, client, mock_db_session):
        response = client.get('/api/auth/me')
        assert response.status_code == 401

    def test_change_password(self, client, mock_db_session):
        # Register & Login
        register_data = {"username": "cpuser", "email": "cp@test.com", "password": "old_password"}
        client.post('/api/auth/register', json=register_data)
        client.post('/api/auth/login', json={"email": "cp@test.com", "password": "old_password"})
        
        # Change Password
        cp_data = {
            "old_password": "old_password",
            "new_password": "new_password"
        }
        response = client.post('/api/auth/change-password', json=cp_data)
        assert response.status_code == 200
        
        # Login with new password
        client.post('/api/auth/logout')
        response = client.post('/api/auth/login', json={"email": "cp@test.com", "password": "new_password"})
        assert response.status_code == 200

    def test_request_password_reset(self, client, mock_db_session):
        register_data = {"username": "resetreq", "email": "req@test.com", "password": "password123"}
        client.post('/api/auth/register', json=register_data)
        
        response = client.post('/api/auth/request-password-reset', json={"email": "req@test.com"})
        assert response.status_code == 200

    def test_reset_password(self, client, mock_db_session):
        register_data = {"username": "resetsucc", "email": "succ@test.com", "password": "old_password"}
        client.post('/api/auth/register', json=register_data)
        
        # Reset Password
        reset_data = {
            "email": "succ@test.com",
            "new_password": "new_password",
            "token": DomainAuthService.MOCK_RESET_TOKEN
        }
        response = client.post('/api/auth/reset-password', json=reset_data)
        assert response.status_code == 200
        
        # Login with new password
        response = client.post('/api/auth/login', json={"email": "succ@test.com", "password": "new_password"})
        assert response.status_code == 200

    def test_reset_password_invalid_token(self, client, mock_db_session):
        register_data = {"username": "resetfail", "email": "fail@test.com", "password": "old_password"}
        client.post('/api/auth/register', json=register_data)
        
        reset_data = {
            "email": "fail@test.com",
            "new_password": "new_password",
            "token": "WRONG_TOKEN"
        }
        response = client.post('/api/auth/reset-password', json=reset_data)
        assert response.status_code == 400
        assert "Invalid password reset token" in response.get_json()['error']
