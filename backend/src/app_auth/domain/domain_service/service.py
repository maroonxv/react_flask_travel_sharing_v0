from abc import ABC, abstractmethod

class PasswordEncoder(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        pass

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        pass
