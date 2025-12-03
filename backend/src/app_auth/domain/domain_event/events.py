from dataclasses import dataclass
from datetime import datetime
from ..value_objects.value_objects import UserId, Email

@dataclass(frozen=True)
class UserRegistered:
    user_id: UserId
    email: Email
    occurred_on: datetime
