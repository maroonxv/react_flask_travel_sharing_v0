import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))
from app_auth.infrastructure.database.persistent_model.user_po import UserPO
from app_auth.infrastructure.database.dao_impl.sqlalchemy_user_dao import SqlAlchemyUserDao

class TestUserDao:
    
    @pytest.fixture
    def user_dao(self, db_session):
        return SqlAlchemyUserDao(db_session)

    def test_add_and_find_by_id(self, user_dao, db_session):
        # Arrange
        user = UserPO(
            id="u1",
            username="testuser",
            email="test@example.com",
            hashed_password="hash",
            role="traveler"
        )
        
        # Act
        user_dao.add(user)
        
        # Assert
        found = user_dao.find_by_id("u1")
        assert found is not None
        assert found.username == "testuser"

    def test_find_by_email(self, user_dao):
        user = UserPO(id="u2", username="u2", email="email@test.com", hashed_password="h", role="guide")
        user_dao.add(user)
        
        found = user_dao.find_by_email("email@test.com")
        assert found is not None
        assert found.id == "u2"
        
        assert user_dao.find_by_email("nonexistent") is None

    def test_find_by_username(self, user_dao):
        user = UserPO(id="u3", username="unique_name", email="e3@t.com", hashed_password="h", role="traveler")
        user_dao.add(user)
        
        found = user_dao.find_by_username("unique_name")
        assert found is not None
        assert found.id == "u3"

    def test_find_by_role(self, user_dao):
        u1 = UserPO(id="r1", username="r1", email="r1@t.com", hashed_password="h", role="admin")
        u2 = UserPO(id="r2", username="r2", email="r2@t.com", hashed_password="h", role="admin")
        u3 = UserPO(id="r3", username="r3", email="r3@t.com", hashed_password="h", role="traveler")
        
        user_dao.add(u1)
        user_dao.add(u2)
        user_dao.add(u3)
        
        admins = user_dao.find_by_role("admin")
        assert len(admins) == 2
        
        travelers = user_dao.find_by_role("traveler")
        # Note: other tests might have added travelers, so we check at least 1
        assert len(travelers) >= 1

    def test_update(self, user_dao, db_session):
        user = UserPO(id="u_update", username="old", email="old@t.com", hashed_password="h", role="traveler")
        user_dao.add(user)
        
        # Detach or query again to ensure update works
        user.username = "new_name"
        user_dao.update(user)
        
        # Verify
        db_session.refresh(user)
        assert user.username == "new_name"
        
        found = user_dao.find_by_id("u_update")
        assert found.username == "new_name"

    def test_delete(self, user_dao):
        user = UserPO(id="u_del", username="del", email="del@t.com", hashed_password="h", role="traveler")
        user_dao.add(user)
        
        user_dao.delete("u_del")
        
        assert user_dao.find_by_id("u_del") is None

    def test_exists(self, user_dao):
        user = UserPO(id="u_exist", username="exist", email="exist@t.com", hashed_password="h", role="traveler")
        user_dao.add(user)
        
        assert user_dao.exists_by_email("exist@t.com") is True
        assert user_dao.exists_by_email("none@t.com") is False
        
        assert user_dao.exists_by_username("exist") is True
        assert user_dao.exists_by_username("none") is False
