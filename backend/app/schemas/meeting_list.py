from datetime import datetime

from pydantic import BaseModel


class MeetingListResponse(BaseModel):

    id: str

    title: str

    status: str

    created_at: datetime

    class Config:
        from_attributes = True