from dataclases import dataclases
from datetime import datetime


@dataclass(frozen=True)
class GeoLocation:
    ...

@dataclass(frozen=True)
class Money:
    ...
@dataclass(frozen=True)
class Budget:
    ...

@dataclass(frozen=True)
class DateRange:
    start_date: datetime
    end_date: datetime