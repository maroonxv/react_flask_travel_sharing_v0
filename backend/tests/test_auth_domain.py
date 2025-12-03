import sys
import os
from datetime import datetime

# Add the src directory to sys.path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from app_auth.domain.value_objects.value_objects import UserId, Email, Password, Role
from app_auth.domain.entity.user import User
from app_auth.domain.domain_event.events import UserRegistered

def test_domain_logic():
    print("Testing Auth Domain Logic...")

    # Test Value Objects
    try:
        email = Email("test@example.com")
        print(f"Email created: {email.value}")
    except ValueError as e:
        print(f"Email creation failed: {e}")
        return

    try:
        invalid_email = Email("invalid-email")
        print("Invalid email check failed (should have raised error)")
    except ValueError:
        print("Invalid email check passed")

    user_id = UserId("user-123")
    password = Password("hashed_secret")

    # Test Entity Creation
    user = User.register(user_id, email, password, "testuser")
    print(f"User registered: {user.username}, Role: {user.role}")

    assert user.id == user_id
    assert user.email == email
    assert user.password == password
    assert user.role == Role.USER

    # Test Domain Logic
    new_password = Password("new_hashed_secret")
    user.change_password(new_password)
    print(f"Password changed. Updated at: {user.updated_at}")
    assert user.password == new_password

    user.update_profile("new_username")
    print(f"Profile updated: {user.username}")
    assert user.username == "new_username"

    # Test Domain Event
    event = UserRegistered(user_id, email, datetime.now())
    print(f"Event created: {event}")

    print("All domain tests passed!")

if __name__ == "__main__":
    test_domain_logic()
