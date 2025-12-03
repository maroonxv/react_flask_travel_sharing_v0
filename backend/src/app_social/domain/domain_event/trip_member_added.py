from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class TripMemberAdded:
    trip_id: int
    member_id: int
    timestamp: datetime