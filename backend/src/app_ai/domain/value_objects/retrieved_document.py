from typing import Optional, Any
from dataclasses import dataclass

@dataclass
class RetrievedDocument:
    content: str
    source_type: str  # 'post' or 'activity'
    reference_id: str
    title: str
    score: float = 0.0
    metadata: Optional[dict] = None

    def __str__(self):
        return f"[{self.source_type.upper()}] {self.title}: {self.content}"
