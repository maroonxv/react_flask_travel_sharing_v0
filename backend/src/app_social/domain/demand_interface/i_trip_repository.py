from typing import List
from domain.trip import Trip
from domain.value_objects import UserId, TripStatus

from abc import ABC, abstractmethod

class ITripRepository(ABC):
    @abstractmethod
    def save(self, trip: Trip):
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, trip_id: int) -> Trip:
        raise NotImplementedError

    @abstractmethod
    def find_by_member(user_id: UserId, status: TripStatus=None) -> List[Trip]:
        raise NotImplementedError

    @abstractmethod
    def find_by_name(name: str) -> List[Trip]:
        raise NotImplementedError

    @abstractmethod
    def remove(self, trip_id: int):
        raise NotImplementedError