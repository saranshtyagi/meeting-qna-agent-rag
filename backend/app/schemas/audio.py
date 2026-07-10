from pydantic import BaseModel


class AudioProcessingResult(BaseModel):

    filename: str

    audio_path: str

    duration: str

    chunks: list[str]