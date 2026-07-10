from pydantic import BaseModel
from datetime import datetime


class MeetingDetailResponse(BaseModel):

    id: str

    title: str

    transcript: str

    summary: str

    action_items: str

    key_decisions: str

    open_questions: str

    youtube_url: str | None = None

    filename: str | None = None

    duration: str | None = None

    status: str

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True