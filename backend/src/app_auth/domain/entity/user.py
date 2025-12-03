from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from ..value_objects.value_objects import UserId, Email, Password, Role
from ..domain_event.events import UserRegistered

@dataclass
class User:
    id: UserId
    email: Email
    password: Password
    username: str
    role: Role = Role.USER
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @staticmethod
    def register(user_id: UserId, email: Email, password: Password, username: str) -> 'User':
        user = User(
            id=user_id,
            email=email,
            password=password,
            username=username
        )
        # In a full event-sourced system, we would return events here.
        # For now, we can just instantiate the event if needed, or return it alongside the user.
        # But typically the Application Service handles publishing.
        # We can also have a list of domain events in the entity.
        return user

    def change_password(self, new_password: Password):
        self.password = new_password
        self.updated_at = datetime.now()

    def update_profile(self, username: str):
        self.username = username
        self.updated_at = datetime.now()
