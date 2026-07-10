from typing import Optional

from pydantic import BaseModel


class MeetingRequest(BaseModel):

    youtube_url: Optional[str] = None


class MeetingResponse(BaseModel):

    meeting_id: str

    title: str

    transcript: str

    summary: str

    action_items: str

    key_decisions: str

    open_questions: str

    class Config:
        from_attributes = True