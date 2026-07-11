from datetime import datetime

from pydantic import BaseModel


class MeetingListResponse(BaseModel):
    id: str
    title: str
    summary: str
    duration: str | None = None
    youtube_url: str | None = None
    filename: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True