import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))
import uuid
from app_auth.domain.entity.user_entity import User
from app_auth.domain.value_objects.user_value_objects import UserId, Email, Username, HashedPassword, UserRole, UserProfile
from app_auth.infrastructure.database.dao_impl.sqlalchemy_user_dao import SqlAlchemyUserDao
from app_auth.infrastructure.database.repository_impl.user_repository_impl import UserRepositoryImpl

class TestUserRepositoryIntegration:
    
    @pytest.fixture
    def user_repo(self, integration_db_session):
        user_dao = SqlAlchemyUserDao(integration_db_session)
        return UserRepositoryImpl(user_dao)

    def test_save_and_find_real_db(self, user_repo):
        # Arrange
        unique_id = str(uuid.uuid4())
        # Use reconstitute or factory method. Direct __init__ might mismatch signature if params are positional.
        # The error "User.__init__() got an unexpected keyword argument 'hashed_password'" suggests __init__ signature issue.
        # Let's use User.reconstitute which is safer for repo tests.
        user = User.reconstitute(
            user_id=UserId(unique_id),
            email=Email(f"test_{unique_id[:8]}@example.com"),
            username=Username(f"user_{unique_id[:8]}"),
            hashed_password=HashedPassword("secret"),
            role=UserRole.USER,
            profile=UserProfile(bio="Integration Test Bio")
        )

        # Act
        user_repo.save(user)

        # Assert
        found_user = user_repo.find_by_id(user.id)
        assert found_user is not None
        assert found_user.email.value == user.email.value
        assert found_user.profile.bio == "Integration Test Bio"

    def test_update_real_db(self, user_repo):
        # Arrange
        unique_id = str(uuid.uuid4())
        user = User.reconstitute(
            user_id=UserId(unique_id),
            email=Email(f"update_{unique_id[:8]}@example.com"),
            username=Username(f"update_{unique_id[:8]}"),
            hashed_password=HashedPassword("secret"),
            role=UserRole.ADMIN
        )
        user_repo.save(user)

        # Act
        # User is immutable or fields are protected. Need to use business method or protected setter if available.
        # Looking at User entity, it has `update_profile` method but that only updates username?
        # Wait, `profile` is protected `_profile`.
        # For test purpose, we might need to use `reconstitute` again or access protected member if python allows.
        # Or use a method like `update_profile` if it exists.
        # The User entity code shows: `_profile = profile`.
        # And no public setter for profile.
        # Actually, let's check `User.update_profile` in `user_entity.py`? No, the user provided code doesn't show `update_profile` updating `UserProfile` object, just `username`.
        # Wait, `user.py` (dataclass) had `update_profile`. `user_entity.py` (rich model) might be different.
        # In `user_entity.py` provided earlier:
        # It has `def update_profile(self, ...)` ? No, I need to check `user_entity.py` content again.
        # It has `_profile`.
        # Let's cheat for integration test and set protected attribute, OR better, add `update_profile_info` method to User entity if needed.
        # But I cannot modify User entity easily without user permission.
        # I will set `_profile` directly since it's python.
        
        new_profile = UserProfile(location="New York")
        user._profile = new_profile # Direct access for test setup
        user_repo.save(user)

        # Assert
        found_user = user_repo.find_by_id(user.id)
        assert found_user.profile.location == "New York"
