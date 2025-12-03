from dataclasses import dataclass



@dataclass(frozen=True)
class MemberId:
    value: int

@dataclass(frozen=True)
class MemberRole:
    value: str