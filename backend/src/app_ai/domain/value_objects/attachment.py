from enum import Enum
from typing import List, Optional
from datetime import datetime

class AttachmentType(Enum):
    POST = "post"
    ACTIVITY = "activity"
    TRIP = "trip"

class MessageAttachment:
    def __init__(self, type: AttachmentType, reference_id: str, title: str, image_url: Optional[str] = None):
        self.type = type
        self.reference_id = reference_id
        self.title = title
        self.image_url = image_url

    def to_dict(self):
        return {
            "type": self.type.value,
            "reference_id": self.reference_id,
            "title": self.title,
            "image_url": self.image_url
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            type=AttachmentType(data["type"]),
            reference_id=data["reference_id"],
            title=data["title"],
            image_url=data.get("image_url")
        )
