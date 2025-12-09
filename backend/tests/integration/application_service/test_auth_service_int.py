import pytest
from flask import Flask
from app_auth.services.auth_application_service import AuthApplicationService
from app_auth.domain.domain_service.auth_service import AuthService as DomainAuthService
from app_auth.infrastructure.database.dao_impl.sqlalchemy_user_dao import SqlAlchemyUserDao
from app_auth.infrastructure.database.repository_impl.user_repository_impl import UserRepositoryImpl
from app_auth.infrastructure.external_service.password_hasher_impl import PasswordHasherImpl
from app_auth.infrastructure.external_service.console_email_service import ConsoleEmailService
from app_auth.domain.value_objects.user_value_objects import UserId

class TestAuthServiceIntegration:
    
    @pytest.fixture
    def flask_app(self):
        app = Flask(__name__)
        app.secret_key = 'test_secret'
        return app

    @pytest.fixture
    def auth_service(self, db_session, flask_app):
        # 1. Infrastructure
        user_dao = SqlAlchemyUserDao(db_session)
        user_repo = UserRepositoryImpl(user_dao)
        password_hasher = PasswordHasherImpl()
        email_service = ConsoleEmailService()
        
        # 2. Domain Service
        domain_service = DomainAuthService(
            user_repo=user_repo,
            password_hasher=password_hasher,
            email_service=email_service
        )
        
        # 3. Application Service
        return AuthApplicationService(
            domain_auth_service=domain_service,
            user_repository=user_repo
        )

    def test_register_success(self, auth_service, flask_app):
        with flask_app.test_request_context():
            user = auth_service.register(
                username="testuser",
                email="test@example.com",
                password="password123"
            )
            
            assert user.username.value == "testuser"
            assert user.email.value == "test@example.com"
            assert user.id is not None
            
            # Verify in DB
            found = auth_service.get_user_by_id(user.id.value)
            assert found is not None
            assert found.username.value == "testuser"

    def test_register_duplicate_username(self, auth_service, flask_app):
        with flask_app.test_request_context():
            auth_service.register("user1", "email1@test.com", "password123")
            
            with pytest.raises(ValueError, match="already exists"):
                auth_service.register("user1", "email2@test.com", "password123")

    def test_register_duplicate_email(self, auth_service, flask_app):
        with flask_app.test_request_context():
            auth_service.register("user1", "email1@test.com", "password123")
            
            with pytest.raises(ValueError, match="already exists"):
                auth_service.register("user2", "email1@test.com", "password123")

    def test_login_success(self, auth_service, flask_app):
        with flask_app.test_request_context() as ctx:
            # Arrange
            auth_service.register("login_user", "login@test.com", "password123")
            
            # Act
            user = auth_service.login("login@test.com", "password123")
            
            # Assert
            assert user is not None
            assert user.username.value == "login_user"
            # Verify session
            from flask import session
            assert session['user_id'] == user.id.value

    def test_login_invalid_password(self, auth_service, flask_app):
        with flask_app.test_request_context():
            auth_service.register("user_wrong_pass", "wrong@test.com", "password123")
            
            user = auth_service.login("wrong@test.com", "wrongpass")
            assert user is None

    def test_login_user_not_found(self, auth_service, flask_app):
        with flask_app.test_request_context():
            user = auth_service.login("nonexistent@test.com", "password123")
            assert user is None

    def test_logout(self, auth_service, flask_app):
        with flask_app.test_request_context() as ctx:
            auth_service.register("logout_user", "logout@test.com", "password123")
            auth_service.login("logout@test.com", "password123")
            
            from flask import session
            assert 'user_id' in session
            
            auth_service.logout()
            assert 'user_id' not in session

    def test_change_password_success(self, auth_service, flask_app):
        with flask_app.test_request_context():
            user = auth_service.register("cp_user", "cp@test.com", "old_password")
            user_id = user.id.value
            
            result = auth_service.change_password(user_id, "old_password", "new_password")
            assert result is True
            
            # Verify new password works
            login_user = auth_service.login("cp@test.com", "new_password")
            assert login_user is not None
            
            # Verify old password fails
            fail_user = auth_service.login("cp@test.com", "old_password")
            assert fail_user is None

    def test_change_password_wrong_old(self, auth_service, flask_app):
        with flask_app.test_request_context():
            user = auth_service.register("cp_fail", "cp_fail@test.com", "old_password")
            
            with pytest.raises(ValueError): # Password mismatch
                auth_service.change_password(user.id.value, "wrong_password", "new_password")

    def test_request_password_reset(self, auth_service, flask_app):
        with flask_app.test_request_context():
            auth_service.register("reset_user", "reset@test.com", "password123")
            
            # Should not raise
            auth_service.request_password_reset("reset@test.com")

    def test_reset_password_success(self, auth_service, flask_app):
        with flask_app.test_request_context():
            auth_service.register("reset_success", "reset_s@test.com", "old_password")
            
            # Use the mock token from domain service
            token = DomainAuthService.MOCK_RESET_TOKEN
            
            auth_service.reset_password("reset_s@test.com", "new_password", token)
            
            # Verify login with new password
            user = auth_service.login("reset_s@test.com", "new_password")
            assert user is not None

    def test_reset_password_invalid_token(self, auth_service, flask_app):
        with flask_app.test_request_context():
            auth_service.register("reset_fail", "reset_f@test.com", "old_password")
            
            with pytest.raises(ValueError, match="Invalid password reset token"):
                auth_service.reset_password("reset_f@test.com", "new_password", "WRONG_TOKEN")

    def test_get_user_by_id(self, auth_service, flask_app):
        with flask_app.test_request_context():
            user = auth_service.register("get_id", "getid@test.com", "password123")
            
            found = auth_service.get_user_by_id(user.id.value)
            assert found is not None
            assert found.id == user.id
            
            not_found = auth_service.get_user_by_id("non_existent_id")
            assert not_found is None
