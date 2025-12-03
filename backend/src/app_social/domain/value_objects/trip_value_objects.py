from dataclasses import dataclass

@dataclass(frozen=True)
class TripId:
    value: int

@dataclass(frozen=True)
class TripName:
    value: str

@dataclass(frozen=True)
class TripDescription:
    value: str

@dataclass(frozen=True)
class TripStartDate:
    value: datetime

@dataclass(frozen=True)
class TripEndDate:
    value: datetime

@dataclass(frozen=True)
class TripBudget:
    value: int

@dataclass(frozen=True)
class TripCurrency:
    value: str

@dataclass(frozen=True)
class TripStatus:
    value: str

@dataclass(frozen=True)
class TripVisibility:
    value: str
