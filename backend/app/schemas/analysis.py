from pydantic import BaseModel


class MeetingAnalysis(BaseModel):

    title: str

    transcript: str

    summary: str

    action_items: str

    key_decisions: str

    open_questions: str