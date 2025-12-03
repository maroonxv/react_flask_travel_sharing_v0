from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional

class Role(Enum):
    USER = "USER"
    ADMIN = "ADMIN"

@dataclass(frozen=True)
class UserId:
    value: str

@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.value):
            raise ValueError("Invalid email format")

@dataclass(frozen=True)
class Password:
    value: str
    # In a real app, we might want to distinguish between raw and hashed passwords here,
    # or just treat this as the "secure" representation.
    # For simplicity in domain, we might just hold the string.
