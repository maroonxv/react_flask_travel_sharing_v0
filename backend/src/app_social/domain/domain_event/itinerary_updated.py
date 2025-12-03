from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class ItineraryUpdated:
    timestamp: datetime