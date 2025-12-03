from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class DestinationRated:
    timestamp: datetime