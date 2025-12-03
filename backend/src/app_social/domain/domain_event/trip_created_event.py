from dataclasses import dataclass

@dataclass(frozen=True)
class TripCreatedEvent:
    trip_id: int
        