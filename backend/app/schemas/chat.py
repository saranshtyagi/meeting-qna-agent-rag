from pydantic import BaseModel


class ChatRequest(BaseModel):

    meeting_id: str

    question: str


class ChatResponse(BaseModel):

    answer: str